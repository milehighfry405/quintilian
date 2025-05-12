import os
from dotenv import load_dotenv
import pvporcupine
import pyaudio
import struct
import threading
import logging
from typing import Callable

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class WakeWordService:
    def __init__(self, wake_word_callback: Callable[[], None]):
        self.wake_word_callback = wake_word_callback
        self.is_running = False
        self.listening_thread = None
        
        # Initialize Porcupine
        access_key = os.getenv('PICOVOICE_ACCESS_KEY')
        if not access_key:
            raise ValueError("PICOVOICE_ACCESS_KEY not found in environment variables")
            
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=['picovoice']
        )
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Find the default input device
        self.device_index = self._find_default_input_device()
        if self.device_index is None:
            raise ValueError("Could not find a default input device")
            
        logger.info(f"Initialized WakeWordService with device index: {self.device_index}")
        
    def _find_default_input_device(self):
        """Find the index of the default input device."""
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info.get('maxInputChannels') > 0:  # If it has input channels
                return i
        return None

    def _listening_loop(self):
        """Main listening loop using Porcupine."""
        try:
            # Open audio stream
            stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.porcupine.frame_length
            )
            
            logger.info("Listening for wake word...")
            
            while self.is_running:
                try:
                    # Read audio data
                    pcm = stream.read(self.porcupine.frame_length)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                    
                    # Process with Porcupine
                    keyword_index = self.porcupine.process(pcm)
                    
                    if keyword_index >= 0:
                        logger.info("Wake word detected!")
                        self.wake_word_callback()
                        
                except Exception as e:
                    logger.error(f"Error in wake word detection: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in wake word service: {e}")
        finally:
            if 'stream' in locals():
                stream.close()

    def start_listening(self):
        """Start listening for wake word in a separate thread."""
        self.is_running = True
        self.listening_thread = threading.Thread(target=self._listening_loop)
        self.listening_thread.start()

    def stop_listening(self):
        """Stop listening for wake word."""
        self.is_running = False
        if self.listening_thread:
            self.listening_thread.join()
        
    def cleanup(self):
        """Clean up resources."""
        self.stop_listening()
        if self.audio:
            self.audio.terminate()
        if self.porcupine:
            self.porcupine.delete()
        logger.info("WakeWordService cleaned up") 