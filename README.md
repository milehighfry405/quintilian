# Smart Household Child Development Assistant

An AI-powered voice assistant that helps families manage toddler activities and development through voice interaction and structured routines.

## 🚀 Quick Start

### Prerequisites
- Windows 10
- PowerShell
- Python 3.8 or higher
- Microphone and speakers

### Installation

1. Clone the repository
2. Navigate to the client directory:
   ```powershell
   cd client
   ```

3. Create and activate virtual environment:
   ```powershell
   python -m venv client-venv
   .\client-venv\Scripts\Activate.ps1
   ```

4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### Running the Assistant

1. Make sure you're in the client directory
2. Activate the virtual environment if not already activated:
   ```powershell
   .\client-venv\Scripts\Activate.ps1
   ```

3. Run the assistant:
   ```powershell
   python openwakeword_assistant.py
   ```

## 📁 Project Structure

```
client/
├── audio/              # Audio files for responses
├── database/           # Local database models and connection
├── legacy/            # Legacy Picovoice implementation
├── tests/             # Test files
├── config.py          # Configuration settings
├── openwakeword_assistant.py  # Main voice assistant implementation
├── prompt_builder.py  # Context-aware prompt generation
└── requirements.txt   # Python dependencies
```

## 🔧 Configuration

- Server URL and other settings can be modified in `config.py`
- Audio settings can be adjusted in the assistant code
- Wake word sensitivity can be tuned in the code

## 🎯 Features

- Wake word detection using OpenWakeWord
- Voice command processing
- Context-aware responses
- Integration with AWS backend
- Audio response generation

## ⚠️ Important Notes

- The server is hosted on AWS and should not be modified locally
- All server code in `/server/` directory is deployed on AWS
- Make sure your microphone and speakers are properly configured
- The assistant requires an internet connection to communicate with the AWS server

## 🐛 Troubleshooting

1. If you get a "No module found" error:
   - Make sure you're in the virtual environment
   - Run `pip install -r requirements.txt` again

2. If audio isn't working:
   - Check your microphone and speaker settings
   - Ensure the audio devices are properly connected

3. If the assistant isn't responding:
   - Check your internet connection
   - Verify the server URL in `config.py`

## 📝 License

This project is proprietary and confidential.

## Deployment Script: server/deploy.py

The `server/deploy.py` script automates deployment of the server's `main.py` to your remote server. It performs the following steps:

1. Copies your local `main.py` to `/home/ubuntu/server/main.py` on the remote server using SCP.
2. Restarts the FastAPI service (assumed to be managed by systemd as `quintilian`).
3. Checks the server health at `http://<SERVER_IP>:8000/health` and prints status updates.

### Usage

1. Ensure your SSH key (`q key.pem`) is in the project root directory.
2. Make sure your local `main.py` is up to date.
3. By default, the script assumes the systemd service is named `quintilian`. If your service has a different name, update the `SERVICE_NAME` variable in `deploy.py`.
4. Run the script from the project root:

```bash
python server/deploy.py
```

The script will print progress and let you know if the deployment was successful or if any errors occurred.

### Prerequisites
- Python 3.x
- `requests` library installed (`pip install requests`)
- SSH access to the server with the specified key
- The remote server must have a systemd service for the FastAPI app 