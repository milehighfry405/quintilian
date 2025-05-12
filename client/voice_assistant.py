import os
import wave
import tempfile
import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
import logging
from wake_word_service import WakeWordService
import threading
import time
from config import SERVER_URL, AUDIO_SETTINGS
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceAssistant:
    def __init__(self):
        self.server_url = SERVER_URL
        self.wake_word_service = WakeWordService(self.on_wake_word_detected)
        self.is_recording = False
        self.processing_thread = None
        self.processing_lock = threading.Lock()
        self.silence_threshold = 10.0  # Keep threshold at 10.0
        self.silence_duration = 1.0  # Increased silence duration to 1.0 seconds
        self.max_recording_duration = 30.0  # Keep max duration at 30 seconds
        self.should_stop_recording = False
        
        # Create audio directory if it doesn't exist
        self.audio_dir = os.path.join(os.path.dirname(__file__), "audio")
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Audio parameters
        self.CHUNK = AUDIO_SETTINGS["CHUNK"]
        self.FORMAT = AUDIO_SETTINGS["FORMAT"]
        self.CHANNELS = AUDIO_SETTINGS["CHANNELS"]
        self.RATE = AUDIO_SETTINGS["RATE"]
        self.RECORD_SECONDS = AUDIO_SETTINGS["RECORD_SECONDS"]
        
        # Generate feedback tones
        self.wake_tone = self.generate_tone(1000, 0.5)  # 1kHz for 0.5 seconds
        self.listening_tone = self.generate_tone(800, 0.3)  # 800Hz for 0.3 seconds
        self.processing_tone = self.generate_tone(600, 0.3)  # 600Hz for 0.3 seconds
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
        
    def on_wake_word_detected(self):
        """Callback when wake word is detected."""
        logger.info("Wake word 'picovoice' detected! Recording your question...")
        self.play_tone(self.wake_tone)  # Play wake word tone
        with self.processing_lock:
            if self.processing_thread is None or not self.processing_thread.is_alive():
                self.should_stop_recording = False
                self.processing_thread = threading.Thread(target=self.record_and_process_question)
                self.processing_thread.start()
            else:
                logger.info("Already processing a question, ignoring wake word")
        
    def download_and_play_audio(self, audio_url, response_text):
        """Download the audio file from the server and play it."""
        full_url = f"{self.server_url}{audio_url}"
        logger.info(f"Downloading audio from {full_url}...")
        response = requests.get(full_url)
        if response.status_code == 200:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"response_{timestamp}.wav"
            filepath = os.path.join(self.audio_dir, filename)
            
            # Save the audio file
            with open(filepath, "wb") as f:
                f.write(response.content)
            logger.info(f"Audio saved as {filepath}")
            
            # Save the text response
            text_filepath = os.path.join(self.audio_dir, f"response_{timestamp}.txt")
            with open(text_filepath, "w") as f:
                f.write(response_text)
            
            # Play the audio
            data, samplerate = sf.read(filepath)
            sd.play(data, samplerate)
            sd.wait()
            
            # Restart wake word detection
            self.wake_word_service.start_listening()
        else:
            logger.error(f"Failed to download audio: {response.status_code}")
        
    def record_until_silence(self):
        """Record audio until silence is detected."""
        logger.info("Starting continuous recording...")
        self.play_tone(self.listening_tone)  # Play listening tone
        
        # Initialize recording
        frames = []
        silence_counter = 0
        is_speaking = False
        start_time = time.time()
        last_speech_time = time.time()
        
        try:
            # Open stream
            stream = sd.InputStream(
                samplerate=self.RATE,
                channels=self.CHANNELS,
                dtype=self.FORMAT
            )
            
            with stream:
                while not self.should_stop_recording:
                    # Check if we've exceeded max duration
                    if time.time() - start_time > self.max_recording_duration:
                        logger.info("Maximum recording duration reached")
                        self.play_tone(self.stop_tone)  # Play stop tone
                        break
                    
                    # Read audio data
                    data, overflowed = stream.read(self.CHUNK)
                    if overflowed:
                        logger.warning("Audio buffer overflow")
                    
                    # Calculate audio level
                    audio_level = np.abs(data).mean()
                    
                    # Log audio level for debugging
                    if len(frames) % 5 == 0:  # Log more frequently
                        logger.info(f"Audio level: {audio_level:.6f}, Silence counter: {silence_counter:.2f}s")
                    
                    # Check for speech or silence
                    if audio_level > self.silence_threshold:
                        is_speaking = True
                        silence_counter = 0
                        last_speech_time = time.time()
                        frames.append(data)
                    elif is_speaking:
                        silence_counter += len(data) / self.RATE
                        frames.append(data)
                        
                        # If silence duration exceeds threshold, stop recording
                        if silence_counter >= self.silence_duration:
                            logger.info(f"Silence detected for {silence_counter:.2f} seconds, stopping recording")
                            self.play_tone(self.stop_tone)  # Play stop tone
                            break
                        
                        # Additional check: if no speech for 3 seconds, stop recording
                        if time.time() - last_speech_time > 3.0:  # Increased to 3 seconds
                            logger.info("No speech detected for 3 seconds, stopping recording")
                            self.play_tone(self.stop_tone)  # Play stop tone
                            break
        except Exception as e:
            logger.error(f"Error during recording: {e}")
            return np.array([])
        
        # Convert frames to numpy array
        if frames:
            recording = np.concatenate(frames, axis=0)
            logger.info(f"Recording finished, duration: {len(recording)/self.RATE:.2f} seconds")
            return recording
        else:
            logger.warning("No audio recorded")
            return np.array([])
        
    def record_and_process_question(self):
        """Record audio after wake word detection and process it."""
        temp_file = None
        try:
            # Record audio until silence
            recording = self.record_until_silence()
            
            # Check if we got any audio
            if len(recording) == 0:
                logger.warning("No audio recorded, skipping processing")
                return
                
            self.play_tone(self.processing_tone)  # Play processing tone
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            logger.info(f"Saving recording to temporary file: {temp_file.name}")
            sf.write(temp_file.name, recording, self.RATE)
            temp_file.close()  # Close the file before sending
                
            # Send to server
            logger.info(f"Sending audio to server at {self.server_url}/process-audio")
            with open(temp_file.name, 'rb') as audio_file:
                try:
                    # Create multipart form data
                    files = {
                        'audio_file': ('audio.wav', audio_file, 'audio/wav')
                    }
                    
                    response = requests.post(
                        f"{self.server_url}/process-audio",
                        files=files
                    )
                    
                    logger.info(f"Server response status: {response.status_code}")
                    if response.status_code != 200:
                        logger.error(f"Server response content: {response.text}")
                        
                    if response.status_code == 200:
                        result = response.json()
                        response_text = result.get('text', 'N/A')
                        logger.info(f"Response text: {response_text}")
                        logger.info(f"Audio URL: {result.get('audio_url', 'N/A')}")
                        
                        # Download and play the response audio
                        self.download_and_play_audio(result.get('audio_url', ''), response_text)
                    else:
                        logger.error(f"Error from server: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request failed: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error processing question: {e}")
        finally:
            # Clean up the temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.error(f"Error cleaning up temporary file: {e}")
            
    def start(self):
        """Start the voice assistant."""
        logger.info("Starting voice assistant...")
        self.wake_word_service.start_listening()
        
    def stop(self):
        """Stop the voice assistant."""
        logger.info("Stopping voice assistant...")
        self.should_stop_recording = True
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish
        self.wake_word_service.cleanup()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    try:
        assistant.start()
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        assistant.stop() 