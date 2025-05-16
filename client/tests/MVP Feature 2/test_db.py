import sqlite3
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_daily_schedule():
    """Check the current schedule in the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect('../../data/quintilian.db')
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().date()
        
        # Query the daily_context table for today's schedule
        cursor.execute("""
            SELECT date, schedule, adjustments, overrides 
            FROM daily_context 
            WHERE date = ?
        """, (today,))
        
        result = cursor.fetchone()
        
        if result:
            date, schedule, adjustments, overrides = result
            logger.info(f"\nDate: {date}")
            logger.info(f"Schedule: {json.dumps(json.loads(schedule), indent=2)}")
            logger.info(f"Adjustments: {json.dumps(json.loads(adjustments), indent=2)}")
            logger.info(f"Overrides: {json.dumps(json.loads(overrides), indent=2)}")
        else:
            logger.error("No schedule found for today")
            
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_daily_schedule() 