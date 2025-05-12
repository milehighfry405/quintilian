from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import openai
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
import tempfile
import json
from pydantic import BaseModel
import logging
import traceback
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create audio directory if it doesn't exist
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Mount the audio directory
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
    raise ValueError("Missing required API keys in environment variables")

# Configure API keys
openai.api_key = OPENAI_API_KEY
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

class AudioResponse(BaseModel):
    text: str
    audio_url: str

class ErrorResponse(BaseModel):
    error: str
    detail: str

@app.post("/process-audio", response_model=AudioResponse, responses={500: {"model": ErrorResponse}})
async def process_audio(audio_file: UploadFile = File(...)):
    try:
        logger.info("Starting audio processing")
        
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            logger.info(f"Saved temporary file to {temp_file_path}")

        # Transcribe audio using Whisper
        logger.info("Starting Whisper transcription")
        with open(temp_file_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        logger.info(f"Transcription completed: {transcript.text}")
        
        # Get GPT-4 response
        logger.info("Getting GPT-4 response")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Quintilian, a helpful and friendly AI assistant. Keep your responses concise and engaging."},
                {"role": "user", "content": transcript.text}
            ]
        )
        
        gpt_response = response.choices[0].message.content
        logger.info(f"GPT-4 response received: {gpt_response}")

        # Generate audio using ElevenLabs
        logger.info("Generating audio with ElevenLabs")
        audio_stream = client.generate(
            text=gpt_response,
            voice=Voice(
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice - a default ElevenLabs voice
                settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
            ),
            model="eleven_monolingual_v1"
        )

        # Save the audio response to the audio directory
        audio_filename = f"response_{os.path.basename(temp_file_path)}"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        # Convert generator to bytes and write to file
        logger.info("Converting audio stream to bytes and saving")
        audio_bytes = b"".join(chunk for chunk in audio_stream)
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        logger.info(f"Audio saved to {audio_path}")

        # Clean up the temporary input file
        os.unlink(temp_file_path)
        logger.info("Temporary file cleaned up")

        return AudioResponse(
            text=gpt_response,
            audio_url=f"/audio/{audio_filename}"
        )

    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Error processing audio: {str(e)}\n{error_detail}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "detail": error_detail
            }
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/ip")
async def get_ip():
    """Return the server's public IP address."""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return {"ip": response.json()["ip"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 