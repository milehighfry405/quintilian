from database import init_db, get_db, FamilyProfile, DailyContext, ActivityLog
from datetime import datetime, timedelta
import json

def test_database_setup():
    # Initialize the database
    init_db()
    print("✅ Database initialized")

    # Get a database session
    db = next(get_db())
    
    try:
        # Create a test family profile
        family = FamilyProfile(
            child_name="Test Child",
            child_age=3,
            preferences={"favorite_color": "blue", "favorite_food": "pizza"}
        )
        db.add(family)
        db.commit()
        print("✅ Family profile created")

        # Create a daily context
        today = datetime.now()
        daily_context = DailyContext(
            family_id=family.id,
            date=today,
            schedule={
                "morning": "Breakfast at 8:00",
                "afternoon": "Nap at 1:00",
                "evening": "Dinner at 6:00"
            }
        )
        db.add(daily_context)
        db.commit()
        print("✅ Daily context created")

        # Create an activity log
        activity = ActivityLog(
            family_id=family.id,
            daily_context_id=daily_context.id,
            activity_name="Breakfast",
            start_time=today.replace(hour=8, minute=0),
            end_time=today.replace(hour=8, minute=30),
            notes="Ate cereal and fruit",
            status="completed"
        )
        db.add(activity)
        db.commit()
        print("✅ Activity log created")

        # Verify the data
        saved_family = db.query(FamilyProfile).first()
        print(f"\nFamily Profile:")
        print(f"Child Name: {saved_family.child_name}")
        print(f"Child Age: {saved_family.child_age}")
        print(f"Preferences: {json.dumps(saved_family.preferences, indent=2)}")

        saved_context = db.query(DailyContext).first()
        print(f"\nDaily Context:")
        print(f"Date: {saved_context.date}")
        print(f"Schedule: {json.dumps(saved_context.schedule, indent=2)}")

        saved_activity = db.query(ActivityLog).first()
        print(f"\nActivity Log:")
        print(f"Activity: {saved_activity.activity_name}")
        print(f"Start Time: {saved_activity.start_time}")
        print(f"End Time: {saved_activity.end_time}")
        print(f"Status: {saved_activity.status}")

        print("\n✅ All database operations successful!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_database_setup() 