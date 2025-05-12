import requests
import base64
import json
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import os

def record_audio(duration=5, sample_rate=16000):
    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    print("Recording finished!")
    return recording

def save_audio(recording, filename="test_audio.wav", sample_rate=16000):
    sf.write(filename, recording, sample_rate)
    print(f"Saved to {filename}")

def download_and_play_audio(audio_url, base_url="http://18.144.166.166:8000"):
    """Download the audio file from the server and play it."""
    full_url = f"{base_url}{audio_url}"
    print(f"Downloading audio from {full_url}...")
    response = requests.get(full_url)
    if response.status_code == 200:
        # Save the audio file locally
        filename = os.path.basename(audio_url)
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Audio saved as {filename}")
        # Play the audio
        data, samplerate = sf.read(filename)
        sd.play(data, samplerate)
        sd.wait()
    else:
        print(f"Failed to download audio: {response.status_code}")

def test_api():
    # API endpoint
    url = "http://18.144.166.166:8000/process-audio"
    
    # Record audio
    recording = record_audio()
    save_audio(recording)
    
    # Prepare the files for the request
    files = {
        'audio_file': ('test_audio.wav', open('test_audio.wav', 'rb'), 'audio/wav')
    }
    
    # Make the request
    print("Sending request to API...")
    response = requests.post(url, files=files)
    
    # Print the response
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nResponse:")
        print(f"Text: {result.get('text', 'N/A')}")
        print(f"Audio URL: {result.get('audio_url', 'N/A')}")
        
        # Play the response audio
        print("\nPlaying response audio...")
        download_and_play_audio(result.get('audio_url', ''))
    else:
        print(f"Error: {response.text}")

def play_audio(audio_base64):
    # Decode base64 to audio data
    audio_bytes = base64.b64decode(audio_base64)
    
    # Save to temporary file
    with open("response.wav", "wb") as f:
        f.write(audio_bytes)
    
    # Play the audio
    data, samplerate = sf.read("response.wav")
    sd.play(data, samplerate)
    sd.wait()

if __name__ == "__main__":
    test_api() 