# Quintilian Voice Assistant

A voice-controlled assistant that uses wake word detection and natural language processing to answer questions. The system consists of a client application that runs locally and a server that processes audio and generates responses.

## Project Structure

```
quintilian-laptop/
├── client/                 # Client application
│   ├── audio/             # Directory for storing audio responses
│   ├── config.py          # Configuration settings
│   ├── requirements.txt   # Python dependencies
│   ├── voice_assistant.py # Main voice assistant implementation
│   └── wake_word_service.py # Wake word detection service
├── server/                # Server application
│   ├── audio/            # Directory for storing server audio files
│   ├── deploy_ec2.py     # EC2 deployment script
│   ├── main.py           # FastAPI server implementation
│   └── requirements.txt  # Server dependencies
├── venv/                  # Server virtual environment (not tracked by git, currently in root)
├── test_api.py           # API testing script
└── .env                  # Environment variables (not in git)
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- AWS account (for server deployment)
- Picovoice account (for wake word detection)

### Client Setup
1. Create a virtual environment:
   ```bash
   cd client
   python -m venv client_venv
   source client_venv/bin/activate  # On Windows: client_venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the client directory with:
   ```
   PICOVOICE_ACCESS_KEY=your_access_key_here
   ```

### Server Setup
1. Create a virtual environment:
   ```bash
   cd server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
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
1. Start the voice assistant:
   ```bash
   cd client
   python voice_assistant.py
   ```

2. Use the wake word "picovoice" to activate the assistant
3. Ask your question after the listening tone
4. Wait for the response

### Audio Feedback
- Wake word detected: 1000Hz tone (0.5s)
- Start recording: 800Hz tone (0.3s)
- Stop recording: 400Hz tone (0.2s)
- Processing: 600Hz tone (0.3s)

## Server Deployment

The server is deployed on AWS EC2 with an Elastic IP (13.57.89.95). The deployment process is automated using the `deploy_ec2.py` script, which:
1. Creates an EC2 instance
2. Sets up the Python environment
3. Installs dependencies
4. Configures the service to run on startup

## File Descriptions

### Client
- `voice_assistant.py`: Main voice assistant implementation with audio recording and processing
- `wake_word_service.py`: Wake word detection using Porcupine
- `config.py`: Configuration settings for the client
- `requirements.txt`: Client dependencies

### Server
- `main.py`: FastAPI server implementation with audio processing endpoints
- `deploy_ec2.py`: EC2 deployment automation script
- `requirements.txt`: Server dependencies

## Testing
- `test_api.py`: Script for testing the server API endpoints

## Notes
- The server uses port 8000
- Audio files are stored in the `client/audio` directory
- The wake word is "picovoice" (default from Porcupine)
- The server is accessible at http://13.57.89.95:8000 