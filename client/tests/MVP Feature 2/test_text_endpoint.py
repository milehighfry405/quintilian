import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVER_URL = "http://13.57.89.95:8000"

def test_process_text():
    # Sample context (mimicking the context sent by the audio flow)
    context = {
        "family": {
            "child_name": "Emma",
            "child_age": 2.5,
            "preferences": {
                "favorite_activities": ["art", "outdoor_play"]
            }
        },
        "daily_context": {
            "schedule": {
                "wake_up": "07:00",
                "breakfast": "07:30",
                "morning_play": "08:00",
                "snack": "10:00",
                "lunch": "12:00",
                "nap": "13:00",
                "afternoon_play": "15:00",
                "dinner": "18:00",
                "bedtime": "19:30"
            },
            "adjustments": {},
            "mood_notes": None
        },
        "recent_activities": [
            {
                "activity_name": "breakfast",
                "start_time": "2025-05-16T07:30:00",
                "end_time": "2025-05-16T08:00:00",
                "status": "completed",
                "notes": None
            },
            {
                "activity_name": "wake_up",
                "start_time": "2025-05-16T07:00:00",
                "end_time": "2025-05-16T07:30:00",
                "status": "completed",
                "notes": None
            }
        ]
    }

    # Sample text input
    text = "Delay nap 30 minutes"

    # Prepare the request payload
    payload = {
        "text": text,
        "context": context
    }

    # Send the request to the /process-text endpoint
    logger.info(f"Sending request to {SERVER_URL}/process-text with payload: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{SERVER_URL}/process-text", json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Response received: {json.dumps(result, indent=2)}")
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_process_text() 