from database import get_db, FamilyProfile, DailyContext, ActivityLog
from datetime import datetime, timedelta
import json

class PromptBuilder:
    def __init__(self):
        self.db = next(get_db())
        
    def get_current_context(self):
        """Get the current family profile and daily context."""
        try:
            # Get the family profile (assuming single family for now)
            family = self.db.query(FamilyProfile).first()
            if not family:
                return None
                
            # Get today's context
            today = datetime.now().date()
            daily_context = self.db.query(DailyContext).filter(
                DailyContext.family_id == family.id,
                DailyContext.date >= today,
                DailyContext.date < today + timedelta(days=1)
            ).first()
            
            # Get recent activities
            recent_activities = self.db.query(ActivityLog).filter(
                ActivityLog.family_id == family.id,
                ActivityLog.start_time >= today
            ).order_by(ActivityLog.start_time.desc()).all()
            
            return {
                "family": family,
                "daily_context": daily_context,
                "recent_activities": recent_activities
            }
        except Exception as e:
            print(f"Error getting context: {e}")
            return None
        finally:
            self.db.close()
            
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