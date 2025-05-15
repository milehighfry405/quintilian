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
        """Record audio after wake word detection and process it."""
        temp_file = None
        try:
            recording = self.record_until_silence()
            
            if len(recording) == 0:
                logger.warning("No audio recorded, skipping processing")
                return
                
            self.play_tone(self.processing_tone)
            
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            logger.info(f"Saving recording to temporary file: {temp_file.name}")
            sf.write(temp_file.name, recording, self.RATE)
            temp_file.close()
                
            logger.info(f"Sending audio to server at {self.server_url}/process-audio")
            with open(temp_file.name, 'rb') as audio_file:
                try:
                    files = {'audio_file': ('audio.wav', audio_file, 'audio/wav')}
                    response = requests.post(f"{self.server_url}/process-audio", files=files)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if 'audio_url' in response_data and 'text' in response_data:
                            self.download_and_play_audio(response_data['audio_url'], response_data['text'])
                        else:
                            logger.error("Invalid response format from server")
                    else:
                        logger.error(f"Server returned error: {response.status_code}")
                        logger.error(f"Server response content: {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error sending audio to server: {e}")
                    
        except Exception as e:
            logger.error(f"Error in record_and_process_question: {e}")
        finally:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                
    def download_and_play_audio(self, audio_url, response_text):
        """Download the audio file from the server and play it."""
        full_url = f"{self.server_url}{audio_url}"
        logger.info(f"Downloading audio from {full_url}...")
        response = requests.get(full_url)
        if response.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"response_{timestamp}.wav"
            filepath = os.path.join(self.audio_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            logger.info(f"Audio saved as {filepath}")
            
            text_filepath = os.path.join(self.audio_dir, f"response_{timestamp}.txt")
            with open(text_filepath, "w") as f:
                f.write(response_text)
            
            data, samplerate = sf.read(filepath)
            sd.play(data, samplerate)
            sd.wait()
            
            # Restart wake word detection
            self.start()
        else:
            logger.error(f"Failed to download audio: {response.status_code}")
            
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