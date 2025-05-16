from fastapi import FastAPI, UploadFile, File, HTTPException, Form
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
from typing import Optional, Dict, Any

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
async def process_audio(
    audio_file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    transcript: Optional[str] = Form(None)
):
    try:
        logger.info("Starting audio processing")
        
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            logger.info(f"Saved temporary file to {temp_file_path}")

        # Parse context if provided
        context_dict = None
        if context:
            try:
                context_dict = json.loads(context)
                logger.info(f"Successfully parsed context JSON: {json.dumps(context_dict, indent=2)}")
            except Exception as e:
                logger.warning(f"Could not parse context JSON: {e}")
                context_dict = None
        
        # Use provided transcript or transcribe audio using Whisper
        if transcript:
            logger.info(f"Using provided transcript: {transcript}")
            transcript_text = transcript
        else:
            logger.info("Starting Whisper transcription")
            with open(temp_file_path, "rb") as audio_file:
                transcript_obj = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            transcript_text = transcript_obj.text
        logger.info(f"Using transcript: {transcript_text}")
        
        # Build the prompt with context if available
        if context_dict:
            logger.info(f"Building prompt with context")
            family = context_dict.get("family", {})
            daily_context = context_dict.get("daily_context", {})
            recent_activities = context_dict.get("recent_activities", [])
            
            system_prompt = f"""You are Quintilian, a helpful and friendly AI assistant for {family.get('child_name', 'the child')} (age {family.get('child_age', 'unknown')}).

Current Schedule:
{json.dumps(daily_context.get('schedule', {}), indent=2) if daily_context.get('schedule') else "No schedule set for today."}

Recent Activities:
{json.dumps([{"name": a.get('activity_name'), "time": a.get('start_time'), "status": a.get('status')} for a in recent_activities], indent=2) if recent_activities else "No recent activities."}

Child's Preferences:
{json.dumps(family.get('preferences', {}), indent=2) if family.get('preferences') else "No preferences set."}

Please respond in a way that:
1. Acknowledges the current schedule and activities
2. Maintains consistency with previous activities
3. Considers the child's preferences
4. Provides helpful, age-appropriate responses"""
            logger.info(f"Built system prompt with context: {system_prompt}")
            user_message = transcript_text  # Just use the transcript directly
        else:
            logger.warning("No context received from client")
            system_prompt = "You are Quintilian, a helpful and friendly AI assistant. Keep your responses concise and engaging."
            user_message = transcript_text
        
        # Get GPT-4 response
        logger.info("Getting GPT-4 response")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
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