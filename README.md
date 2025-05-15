# Quintilian Voice Assistant

A voice-controlled assistant that uses wake word detection and natural language processing to answer questions. The system consists of a client application that runs locally and a server that processes audio and generates responses.

## Project Structure

```
quintilian/
├── client/                 # Client application
│   ├── audio/             # Directory for storing audio responses
│   ├── config.py          # Configuration settings
│   ├── requirements.txt   # Python dependencies
│   ├── picovoice_assistant.py # Picovoice implementation
│   ├── picovoice_wake_word_service.py # Picovoice wake word service
│   ├── openwakeword_assistant.py # OpenWakeWord implementation
│   └── test_openwakeword.py # OpenWakeWord test script
├── server/                # Server application
│   ├── audio/            # Directory for storing server audio files
│   ├── deploy_ec2.py     # EC2 deployment script
│   ├── main.py           # FastAPI server implementation
│   └── requirements.txt  # Server dependencies
├── venv/                  # Server virtual environment (not tracked by git)
├── test_api.py           # API testing script
└── .env                  # Environment variables (not in git)
```

## Wake Word Implementations

The project provides two different wake word detection implementations:

### 1. Picovoice Implementation
- **Files:**
  - `picovoice_assistant.py`: Main assistant implementation using Picovoice
  - `picovoice_wake_word_service.py`: Wake word detection service using Picovoice
- **Wake Word System:** Picovoice Porcupine
- **Requirements:**
  - Picovoice access key (required)
  - PyAudio
  - pvporcupine
- **Wake Word:** "Hey Jarvis"

### 2. OpenWakeWord Implementation
- **Files:**
  - `openwakeword_assistant.py`: Main assistant implementation using OpenWakeWord
  - `test_openwakeword.py`: Test script for OpenWakeWord implementation
- **Wake Word System:** OpenWakeWord
- **Requirements:**
  - sounddevice
  - numpy
  - openwakeword
- **Wake Word:** "Hey Jarvis"

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- AWS account (for server deployment)
- Picovoice account (for Picovoice implementation only)

### Client Setup
1. Create a virtual environment:
   ```bash
   cd client
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. For Picovoice implementation, create a `.env` file in the client directory:
   ```
   PICOVOICE_ACCESS_KEY=your_access_key_here
   ```

### Server Setup
1. Create a virtual environment:
   ```bash
   cd server
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Deploy to EC2:
   ```bash
   python deploy_ec2.py
   ```

## Usage

### Running the Voice Assistant

#### Picovoice Implementation
```bash
cd client
python picovoice_assistant.py
```

#### OpenWakeWord Implementation
```bash
cd client
python openwakeword_assistant.py
```

### Audio Feedback
- Wake word detected: 1000Hz tone (0.5s)
- Start recording: 800Hz tone (0.3s)
- Stop recording: 400Hz tone (0.2s)
- Processing: 600Hz tone (0.3s)

## Configuration

### Picovoice Configuration
- Requires a valid Picovoice access key
- Wake word sensitivity can be adjusted in `picovoice_wake_word_service.py`
- Audio settings are configured in `config.py`

### OpenWakeWord Configuration
- No API key required
- Wake word sensitivity can be adjusted in `openwakeword_assistant.py`
- Audio settings are configured in `config.py`

### Audio Settings
- Sample Rate: 16000 Hz
- Channels: 1 (Mono)
- Format: 16-bit PCM
- Chunk Size: 1024 samples

## Server Deployment

The server is deployed on AWS EC2 with an Elastic IP (13.57.89.95). The deployment process is automated using the `deploy_ec2.py` script, which:
1. Creates an EC2 instance
2. Sets up the Python environment
3. Installs dependencies
4. Configures the service to run on startup

## Notes
- The server uses port 8000
- Audio files are stored in the `client/audio` directory
- The OpenWakeWord implementation is free to use and doesn't require an API key
- The Picovoice implementation requires a valid access key but may provide better wake word detection
- Both implementations use the same backend server for processing commands
- The server is accessible at http://13.57.89.95:8000 