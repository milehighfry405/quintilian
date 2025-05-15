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