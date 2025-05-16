import sqlite3
import json
from datetime import datetime

DB_PATH = "../../quintilian.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            schedule TEXT,
            adjustments TEXT,
            overrides TEXT,
            mood_notes TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # Insert a sample schedule for today if not exists
    today = datetime.now().date().isoformat()
    cursor.execute('''
        SELECT id FROM daily_context WHERE date(date) = date(?)
    ''', (today,))
    if not cursor.fetchone():
        schedule = {
            "wake_up": "07:00",
            "breakfast": "07:30",
            "morning_play": "08:00",
            "snack": "10:00",
            "lunch": "12:00",
            "nap": "13:00",
            "afternoon_play": "15:00",
            "dinner": "18:00",
            "bedtime": "19:30"
        }
        cursor.execute('''
            INSERT INTO daily_context (date, schedule, adjustments, overrides, mood_notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            today,
            json.dumps(schedule),
            json.dumps({}),
            json.dumps({}),
            None,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        print(f"Inserted sample schedule for {today}")
    else:
        print(f"Schedule for {today} already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.") 