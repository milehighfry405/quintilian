import requests
import json
import logging
from datetime import datetime
import sqlite3
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVER_URL = "http://13.57.89.95:8000"
DB_PATH = "../../quintilian.db"  # Path to the client's SQLite database

def get_current_schedule():
    """Get the current schedule from the client's database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get today's schedule
        today = datetime.now().date()
        cursor.execute("""
            SELECT schedule, adjustments 
            FROM daily_context 
            WHERE date(date) = date(?)
        """, (today.isoformat(),))
        
        result = cursor.fetchone()
        if result:
            schedule, adjustments = result
            return {
                "schedule": json.loads(schedule) if schedule else {},
                "adjustments": json.loads(adjustments) if adjustments else {}
            }
        return None
    except Exception as e:
        logger.error(f"Error getting schedule from database: {e}")
        return None
    finally:
        conn.close()

def update_schedule(new_schedule, adjustments):
    """Update the schedule in the client's database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        cursor.execute("""
            UPDATE daily_context 
            SET schedule = ?, adjustments = ?, updated_at = ?
            WHERE date(date) = date(?)
        """, (
            json.dumps(new_schedule),
            json.dumps(adjustments),
            datetime.now().isoformat(),
            today.isoformat()
        ))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating schedule in database: {e}")
        return False
    finally:
        conn.close()

def test_delay_nap():
    """Test the nap delay functionality."""
    # Get current schedule from database
    current_context = get_current_schedule()
    if not current_context:
        logger.error("No schedule found for today")
        return
    
    # Prepare the context for the server
    context = {
        "family": {
            "child_name": "Emma",
            "child_age": 2.5,
            "preferences": {
                "favorite_activities": ["art", "outdoor_play"]
            }
        },
        "daily_context": {
            "schedule": current_context["schedule"],
            "adjustments": current_context["adjustments"],
            "mood_notes": None
        },
        "recent_activities": []
    }
    
    # Send the delay command
    text = "Delay nap 30 minutes"
    payload = {
        "text": text,
        "context": context
    }
    
    logger.info(f"Sending request to {SERVER_URL}/process-text with payload: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{SERVER_URL}/process-text", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Response received: {json.dumps(result, indent=2)}")
        
        # Update the local database with the changes
        if "schedule" in result:
            success = update_schedule(
                result["schedule"],
                result.get("adjustments", {})
            )
            if success:
                logger.info("Successfully updated schedule in database")
            else:
                logger.error("Failed to update schedule in database")
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_delay_nap() 