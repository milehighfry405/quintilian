from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class FamilyProfile(Base):
    __tablename__ = "family_profile"

    id = Column(Integer, primary_key=True, index=True)
    child_name = Column(String(100), nullable=False)
    child_age = Column(Integer, nullable=False)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    daily_contexts = relationship("DailyContext", back_populates="family")
    activity_logs = relationship("ActivityLog", back_populates="family")

class DailyContext(Base):
    __tablename__ = "daily_context"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_profile.id"))
    date = Column(DateTime, nullable=False)
    schedule = Column(JSON, default={})  # Stores the day's schedule
    adjustments = Column(JSON, default={})  # Stores any schedule adjustments
    overrides = Column(JSON, default={})  # Stores any schedule overrides
    mood_notes = Column(Text)  # Any notes about the child's mood
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    family = relationship("FamilyProfile", back_populates="daily_contexts")
    activities = relationship("ActivityLog", back_populates="daily_context")

class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_profile.id"))
    daily_context_id = Column(Integer, ForeignKey("daily_context.id"))
    activity_name = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    notes = Column(Text)
    status = Column(String(50), default="completed")  # completed, skipped, in_progress
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    family = relationship("FamilyProfile", back_populates="activity_logs")
    daily_context = relationship("DailyContext", back_populates="activities") 