import os
import wave
import tempfile
import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
import logging
import threading
import time
from datetime import datetime
import openwakeword
from openwakeword.model import Model
from config import SERVER_URL, AUDIO_SETTINGS
from prompt_builder import PromptBuilder
import json
from sqlalchemy import func
import traceback

print("Starting OpenWakeWord Assistant...")  # Test print statement

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenVoiceAssistant:
    def __init__(self):
        self.server_url = SERVER_URL
        self.is_recording = False
        self.processing_thread = None
        self.processing_lock = threading.Lock()
        self.silence_threshold = 60.0
        self.silence_duration = 1.0
        self.max_recording_duration = 30.0
        self.should_stop_recording = False
        self.last_wake_word_time = 0
        self.wake_word_cooldown = 2.0
        self.prompt_builder = PromptBuilder()
        
        # Create audio directory if it doesn't exist
        self.audio_dir = os.path.join(os.path.dirname(__file__), "audio")
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Audio parameters
        self.CHUNK = AUDIO_SETTINGS["CHUNK"]
        self.FORMAT = AUDIO_SETTINGS["FORMAT"]
        self.CHANNELS = AUDIO_SETTINGS["CHANNELS"]
        self.RATE = AUDIO_SETTINGS["RATE"]
        self.RECORD_SECONDS = AUDIO_SETTINGS["RECORD_SECONDS"]
        
        # Initialize openWakeWord
        openwakeword.utils.download_models()
        self.model = Model(
            wakeword_models=["hey_jarvis"],  # Using hey_jarvis as wake word
            inference_framework="onnx"  # Using ONNX for better Windows compatibility
        )
        
        # Generate feedback tones
        self.wake_tone = self.generate_tone(1000, 0.5)  # 1kHz for 0.5 seconds
        self.listening_tone = self.generate_tone(800, 0.3)  # 800Hz for 0.3 seconds
        self.processing_tone = self.generate_tone(600, 0.3)
        self.stop_tone = self.generate_tone(400, 0.2)  # 400Hz for 0.2 seconds
        
    def generate_tone(self, frequency, duration):
        """Generate a simple sine wave tone."""
        t = np.linspace(0, duration, int(self.RATE * duration), False)
        tone = np.sin(2 * np.pi * frequency * t)
        return tone
        
    def play_tone(self, tone):
        """Play a tone through the default audio device."""
        sd.play(tone, self.RATE)
        sd.wait()
        
    def listen_for_wake_word(self):
        """Continuously listen for wake word."""
        logger.info("Listening for wake word...")
        stream = sd.InputStream(
            samplerate=self.RATE,
            channels=self.CHANNELS,
            dtype=self.FORMAT
        )
        
        with stream:
            while not self.should_stop_recording:
                data, overflowed = stream.read(self.CHUNK)
                if overflowed:
                    logger.warning("Audio buffer overflow")
                
                # Get prediction from openWakeWord
                prediction = self.model.predict(data.flatten())
                
                # Check if wake word was detected with higher threshold and cooldown
                current_time = time.time()
                if (prediction["hey_jarvis"] > 0.6 and
                    current_time - self.last_wake_word_time > self.wake_word_cooldown):
                    logger.info("Wake word detected! Recording your question...")
                    self.last_wake_word_time = current_time
                    self.play_tone(self.wake_tone)
                    with self.processing_lock:
                        if self.processing_thread is None or not self.processing_thread.is_alive():
                            self.should_stop_recording = False
                            self.processing_thread = threading.Thread(target=self.record_and_process_question)
                            self.processing_thread.start()
                        else:
                            logger.info("Already processing a question, ignoring wake word")
        
    def record_until_silence(self):
        """Record audio until silence is detected."""
        logger.info("Starting continuous recording...")
        self.play_tone(self.listening_tone)
        
        frames = []
        silence_counter = 0
        is_speaking = False
        start_time = time.time()
        last_speech_time = time.time()
        
        try:
            stream = sd.InputStream(
                samplerate=self.RATE,
                channels=self.CHANNELS,
                dtype=self.FORMAT
            )
            
            with stream:
                while not self.should_stop_recording:
                    if time.time() - start_time > self.max_recording_duration:
                        logger.info("Maximum recording duration reached")
                        self.play_tone(self.stop_tone)
                        break
                    
                    data, overflowed = stream.read(self.CHUNK)
                    if overflowed:
                        logger.warning("Audio buffer overflow")
                    
                    audio_level = np.abs(data).mean()
                    
                    if len(frames) % 5 == 0:
                        logger.info(f"Audio level: {audio_level:.6f}, Silence counter: {silence_counter:.2f}s")
                    
                    if audio_level > self.silence_threshold:
                        is_speaking = True
                        silence_counter = 0
                        last_speech_time = time.time()
                        frames.append(data)
                    elif is_speaking:
                        # Calculate time since last speech
                        time_since_speech = time.time() - last_speech_time
                        silence_counter = time_since_speech
                        frames.append(data)
                        
                        if silence_counter >= self.silence_duration:
                            logger.info(f"Silence detected for {silence_counter:.2f} seconds, stopping recording")
                            self.play_tone(self.stop_tone)
                            break
                        
                        if time_since_speech > 3.0:
                            logger.info("No speech detected for 3 seconds, stopping recording")
                            self.play_tone(self.stop_tone)
                            break
        except Exception as e:
            logger.error(f"Error during recording: {e}")
            return np.array([])
        
        if frames:
            recording = np.concatenate(frames, axis=0)
            logger.info(f"Recording finished, duration: {len(recording)/self.RATE:.2f} seconds")
            return recording
        else:
            logger.warning("No audio recorded")
            return np.array([])
        
    def record_and_process_question(self):
        try:
            logger.info("Wake word detected! Recording your question...")
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.close()  # Close the file so it can be used by sounddevice
            
            logger.info("Starting continuous recording...")
            recording = self.record_until_silence()
            logger.info(f"Recording finished, duration: {len(recording)/self.RATE:.2f} seconds")
            
            logger.info(f"Saving recording to temporary file: {temp_file.name}")
            sf.write(temp_file.name, recording, self.RATE)
            
            # Get context from database
            context = self.prompt_builder.get_current_context()
            logger.info(f"Got context from database: {context}")
            
            # Convert context to dictionary format
            context_dict = {
                "family": {
                    "child_name": context["family"].child_name,
                    "child_age": context["family"].child_age,
                    "preferences": context["family"].preferences
                },
                "daily_context": {
                    "schedule": context["daily_context"].schedule,
                    "adjustments": context["daily_context"].adjustments,
                    "mood_notes": context["daily_context"].mood_notes
                },
                "recent_activities": [
                    {
                        "activity_name": activity.activity_name,
                        "start_time": activity.start_time.isoformat(),
                        "end_time": activity.end_time.isoformat() if activity.end_time else None,
                        "status": activity.status,
                        "notes": activity.notes
                    }
                    for activity in context["recent_activities"]
                ]
            }
            logger.info(f"Converted context to dictionary: {json.dumps(context_dict, indent=2)}")
            
            # Prepare the request
            files = {
                'audio_file': ('audio.wav', open(temp_file.name, 'rb'), 'audio/wav')
            }
            data = {
                'context': json.dumps(context_dict),
                'transcript': None
            }
            
            logger.info("Request details:")
            logger.info(f"Files: {files}")
            logger.info(f"Data: {data}")
            
            # Send the request
            logger.info(f"Sending audio to server at {self.server_url}/process-audio")
            logger.info(f"Sending request with data: {json.dumps(data, indent=2)}")
            response = requests.post(
                f"{self.server_url}/process-audio",
                files=files,
                data=data
            )
            
            # Close the file handle
            files['audio_file'][1].close()
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if there's an action in the response
                if response_data.get('action'):
                    action = response_data['action']
                    logger.info(f"Action detected: {json.dumps(action, indent=2)}")
                    
                    if action['type'] == 'update_schedule':
                        # Update the schedule in the database
                        self.update_schedule({
                            "activity_name": action['activity'],
                            "new_time": action['new_start_time']
                        })
                
                # Play the audio response
                if response_data.get('audio_url'):
                    audio_url = response_data['audio_url']  # Don't prefix with server_url since it's already included
                    logger.info(f"Playing audio response from: {audio_url}")
                    self.download_and_play_audio(audio_url)
            else:
                logger.error(f"Server returned error: {response.status_code}")
                logger.error(f"Server response content: {response.text}")
                
        except Exception as e:
            logger.error(f"Error in record_and_process_question: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            # Try to clean up the temporary file, but don't fail if we can't
            try:
                if 'temp_file' in locals():
                    os.unlink(temp_file.name)
                    logger.info("Temporary file cleaned up")
            except Exception as e:
                logger.warning(f"Could not clean up temporary file: {str(e)}")
                
    def update_schedule(self, modification):
        """Update the schedule in the database based on server response."""
        try:
            from database import get_db, DailyContext
            from datetime import datetime
            
            db = next(get_db())
            today = datetime.now().date()
            
            # Get today's context
            daily_context = db.query(DailyContext).filter(
                func.date(DailyContext.date) == today
            ).first()
            
            if not daily_context:
                logger.error("No daily context found for today")
                return False
                
            # Update the schedule
            schedule = daily_context.schedule or {}
            activity_name = modification["activity_name"]
            new_time = modification["new_time"]
            logger.info(f"Schedule before update: {schedule}")
            
            if activity_name in schedule:
                # Store original time before updating
                original_time = schedule[activity_name]
                
                # Update the schedule
                schedule[activity_name] = new_time
                
                # Add to adjustments
                adjustments = daily_context.adjustments or {}
                if activity_name not in adjustments:
                    adjustments[activity_name] = {}
                    
                adjustments[activity_name] = {
                    "original_time": original_time,
                    "new_time": new_time,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Update the database
                daily_context.schedule = schedule
                daily_context.adjustments = adjustments
                logger.info(f"Schedule after update: {daily_context.schedule}")
                db.commit()
                logger.info(f"Successfully updated schedule for {activity_name}")
                return True
            else:
                logger.error(f"Activity {activity_name} not found in schedule")
                return False
                
        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            logger.error(traceback.format_exc())
            db.rollback()
            return False
        finally:
            db.close()

    def process_gpt_response(self, response_text):
        """Process GPT response for schedule modifications."""
        try:
            # Check if the response indicates a schedule modification
            if "delay" in response_text.lower() and "minutes" in response_text.lower():
                # Extract modification details from the response
                import re
                
                # Look for patterns like "delay X minutes" or "postpone by X minutes"
                delay_match = re.search(r'(?:delay|postpone).*?(\d+).*?minutes', response_text.lower())
                if delay_match:
                    delay_minutes = int(delay_match.group(1))
                    
                    # Look for activity name (this is a simple implementation)
                    activity_match = re.search(r'(?:delay|postpone)\s+(\w+)', response_text.lower())
                    if activity_match:
                        activity_name = activity_match.group(1)
                        
                        # Get current schedule to find original time
                        from database import get_db, DailyContext
                        from datetime import datetime
                        
                        db = next(get_db())
                        today = datetime.now().date()
                        daily_context = db.query(DailyContext).filter(
                            func.date(DailyContext.date) == today
                        ).first()
                        
                        if daily_context and daily_context.schedule:
                            schedule = daily_context.schedule
                            if activity_name in schedule:
                                original_time = schedule[activity_name]["time"]
                                
                                # Calculate new time
                                from datetime import datetime, timedelta
                                original_dt = datetime.strptime(original_time, "%H:%M")
                                new_dt = original_dt + timedelta(minutes=delay_minutes)
                                new_time = new_dt.strftime("%H:%M")
                                
                                # Log the modification details
                                logger.info(f"Modifying schedule: {activity_name} from {original_time} to {new_time} (delay: {delay_minutes} minutes)")
                                
                                # Send modification to server
                                modification = {
                                    "activity_name": activity_name,
                                    "delay_minutes": delay_minutes,
                                    "original_time": original_time,
                                    "new_time": new_time
                                }
                                
                                response = requests.post(
                                    f"{self.server_url}/modify-schedule",
                                    json=modification
                                )
                                
                                if response.status_code == 200:
                                    # Update local database
                                    success = self.update_schedule(modification)
                                    if success:
                                        logger.info("Schedule updated successfully in local database.")
                                    else:
                                        logger.error("Failed to update schedule in local database.")
                                    return success
                                else:
                                    logger.error(f"Server returned status code {response.status_code} for schedule modification.")
                        else:
                            logger.error("No daily context or schedule found for today.")
            return False
        except Exception as e:
            logger.error(f"Error processing GPT response: {e}")
            return False
            
    def download_and_play_audio(self, audio_url):
        """Download and play audio response."""
        try:
            # Download and play the audio
            response = requests.get(f"{self.server_url}{audio_url}")
            if response.status_code == 200:
                audio_data = response.content
                audio_file = os.path.join(self.audio_dir, "response.wav")
                with open(audio_file, "wb") as f:
                    f.write(audio_data)
                
                # Play the audio
                data, samplerate = sf.read(audio_file)
                sd.play(data, samplerate)
                sd.wait()
                
                # Clean up
                os.remove(audio_file)
            else:
                logger.error(f"Failed to download audio: {response.status_code}")
        except Exception as e:
            logger.error(f"Error playing audio: {e}")

    def start(self):
        """Start the voice assistant."""
        logger.info("Starting OpenVoice Assistant...")
        self.should_stop_recording = False
        self.listen_for_wake_word()
        
    def stop(self):
        """Stop the voice assistant."""
        logger.info("Stopping OpenVoice Assistant...")
        self.should_stop_recording = True
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join()

if __name__ == "__main__":
    try:
        assistant = OpenVoiceAssistant()
        print("Assistant created, starting...")
        assistant.start()
    except KeyboardInterrupt:
        print("\nStopping assistant...")
        assistant.stop()
    except Exception as e:
        print(f"Error: {e}")
        if 'assistant' in locals():
            assistant.stop() 