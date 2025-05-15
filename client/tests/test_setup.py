from database import init_db, get_db, FamilyProfile, DailyContext, ActivityLog
from datetime import datetime, timedelta
import json

def setup_test_data():
    # Initialize the database
    init_db()
    print("✅ Database initialized")

    # Get a database session
    db = next(get_db())
    
    try:
        # Create a test family profile
        family = FamilyProfile(
            child_name="Emma",
            child_age=3,
            preferences={
                "favorite_color": "purple",
                "favorite_food": "pizza",
                "favorite_activities": ["dancing", "painting", "reading"],
                "bedtime": "7:30 PM",
                "naptime": "1:00 PM"
            }
        )
        db.add(family)
        db.commit()
        print("✅ Family profile created")

        # Create today's context
        today = datetime.now()
        daily_context = DailyContext(
            family_id=family.id,
            date=today,
            schedule={
                "morning": {
                    "7:00 AM": "Wake up",
                    "7:30 AM": "Breakfast",
                    "8:30 AM": "Learning activities"
                },
                "afternoon": {
                    "12:00 PM": "Lunch",
                    "1:00 PM": "Nap time",
                    "3:00 PM": "Creative play"
                },
                "evening": {
                    "5:30 PM": "Dinner",
                    "6:30 PM": "Bath time",
                    "7:30 PM": "Bedtime routine"
                }
            },
            adjustments={
                "nap_time": "Delayed by 30 minutes"
            },
            mood_notes="Emma is in a good mood today, excited about painting"
        )
        db.add(daily_context)
        db.commit()
        print("✅ Daily context created")

        # Create some activity logs
        activities = [
            ActivityLog(
                family_id=family.id,
                daily_context_id=daily_context.id,
                activity_name="Breakfast",
                start_time=today.replace(hour=7, minute=30),
                end_time=today.replace(hour=8, minute=0),
                notes="Ate cereal and fruit, drank milk",
                status="completed"
            ),
            ActivityLog(
                family_id=family.id,
                daily_context_id=daily_context.id,
                activity_name="Learning activities",
                start_time=today.replace(hour=8, minute=30),
                end_time=today.replace(hour=9, minute=30),
                notes="Practiced counting and colors",
                status="completed"
            ),
            ActivityLog(
                family_id=family.id,
                daily_context_id=daily_context.id,
                activity_name="Creative play",
                start_time=today.replace(hour=3, minute=0),
                end_time=None,
                notes="Started painting with purple paint",
                status="in_progress"
            )
        ]
        
        for activity in activities:
            db.add(activity)
        db.commit()
        print("✅ Activity logs created")

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
        print(f"Adjustments: {json.dumps(saved_context.adjustments, indent=2)}")
        print(f"Mood Notes: {saved_context.mood_notes}")

        saved_activities = db.query(ActivityLog).all()
        print(f"\nActivity Logs:")
        for activity in saved_activities:
            print(f"- {activity.activity_name} ({activity.start_time.strftime('%I:%M %p')}) - {activity.status}")

        print("\n✅ All test data setup complete!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_test_data() 