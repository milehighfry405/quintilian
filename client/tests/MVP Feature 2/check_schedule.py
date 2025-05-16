import sqlite3
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "../../quintilian.db"

def check_current_schedule():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        cursor.execute("""
            SELECT schedule, adjustments, updated_at 
            FROM daily_context 
            WHERE date(date) = date(?)
        """, (today.isoformat(),))
        
        result = cursor.fetchone()
        if result:
            schedule = json.loads(result[0])
            adjustments = json.loads(result[1])
            updated_at = result[2]
            
            logger.info(f"Current Schedule (last updated: {updated_at}):")
            logger.info(json.dumps(schedule, indent=2))
            
            if adjustments:
                logger.info("\nRecent Adjustments:")
                logger.info(json.dumps(adjustments, indent=2))
        else:
            logger.error("No schedule found for today")
            
    except Exception as e:
        logger.error(f"Error reading schedule: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_current_schedule() 