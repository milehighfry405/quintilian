"""
Configuration for the Quintilian voice assistant.
"""

# The domain name that will point to your server
SERVER_DOMAIN = "13.57.89.95"

# The base URL for the server
SERVER_URL = f"http://{SERVER_DOMAIN}:8000"

# Wake word settings
WAKE_WORD = "hey_jarvis"

# Audio settings
AUDIO_SETTINGS = {
    "CHUNK": 1024,
    "FORMAT": 'int16',
    "CHANNELS": 1,
    "RATE": 16000,
    "RECORD_SECONDS": 5
} 