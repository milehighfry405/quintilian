from database import get_db, FamilyProfile, DailyContext, ActivityLog
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)

class PromptBuilder:
    def __init__(self):
        pass
        
    def get_current_context(self):
        """Get current context from database"""
        try:
            db = next(get_db())
            logger.info("Getting family profile from database")
            family = db.query(FamilyProfile).first()
            logger.info(f"Found family profile: {family}")
            
            if not family:
                logger.warning("No family profile found in database")
                return None
            
            logger.info("Getting today's context from database")
            today = datetime.now().date()
            daily_context = db.query(DailyContext).filter(
                func.date(DailyContext.date) == today,
                DailyContext.family_id == family.id
            ).first()
            logger.info(f"Found daily context: {daily_context}")
            
            logger.info("Getting recent activities from database")
            recent_activities = db.query(ActivityLog).filter(
                ActivityLog.start_time >= datetime.now() - timedelta(hours=24)
            ).order_by(ActivityLog.start_time.desc()).all()
            logger.info(f"Found {len(recent_activities)} recent activities")
            
            context = {
                "family": family,
                "daily_context": daily_context,
                "recent_activities": recent_activities
            }
            logger.info(f"Returning context: {context}")
            return context
        except Exception as e:
            logger.error(f"Error getting context from database: {e}")
            return None
        finally:
            db.close()
            
    def build_prompt(self, user_input):
        """Build a context-aware prompt for GPT-4."""
        context = self.get_current_context()
        if not context:
            return user_input
            
        family = context["family"]
        daily_context = context["daily_context"]
        recent_activities = context["recent_activities"]
        
        # Build the context string
        context_str = f"""You are Quintilian, a helpful and friendly AI assistant for {family.child_name} (age {family.child_age}).

Current Schedule:
{json.dumps(daily_context.schedule, indent=2) if daily_context and daily_context.schedule else "No schedule set for today."}

Recent Activities:
{self._format_activities(recent_activities) if recent_activities else "No recent activities."}

Child's Preferences:
{json.dumps(family.preferences, indent=2) if family.preferences else "No preferences set."}

User's Question/Command: {user_input}

Please respond in a way that:
1. Acknowledges the current schedule and activities
2. Maintains consistency with previous activities
3. Considers the child's preferences
4. Provides helpful, age-appropriate responses
"""
        return context_str
        
    def _format_activities(self, activities):
        """Format activities for the prompt."""
        if not activities:
            return "No activities recorded."
            
        formatted = []
        for activity in activities:
            status = "✅" if activity.status == "completed" else "⏳" if activity.status == "in_progress" else "❌"
            formatted.append(f"{status} {activity.activity_name} ({activity.start_time.strftime('%I:%M %p')})")
            
        return "\n".join(formatted) 