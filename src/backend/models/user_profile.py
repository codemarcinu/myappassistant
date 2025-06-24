from datetime import datetime, time
from enum import Enum
from typing import Any, Dict, List, Optional

import pytz
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

# Removed unused import


class InteractionType(str, Enum):
    """Types of user interactions for analysis"""

    QUERY = "query"
    CLICK = "click"
    FEEDBACK = "feedback"
    SETTING_CHANGE = "setting_change"
    FILE_UPLOAD = "file_upload"
    CHAT = "chat"


class Formality(str, Enum):
    """Communication style formality options"""

    FORMAL = "formal"
    NEUTRAL = "neutral"
    CASUAL = "casual"


class UserPreferences(BaseModel):
    """User preferences for personalization"""

    formality: Formality = Formality.NEUTRAL
    news_topics: List[str] = []
    favorite_locations: List[str] = []
    notifications_enabled: bool = True
    daily_summary_enabled: bool = False
    alert_severe_weather: bool = True
    time_format_24h: bool = True
    temperature_unit: str = "celsius"


class UserSchedule(BaseModel):
    """User schedule preferences for automated suggestions"""

    wake_time: time = Field(default_factory=lambda: time(7, 0))
    sleep_time: time = Field(default_factory=lambda: time(23, 0))
    work_days: List[int] = [0, 1, 2, 3, 4]  # Monday=0, Sunday=6
    work_start_time: time = Field(default_factory=lambda: time(9, 0))
    work_end_time: time = Field(default_factory=lambda: time(17, 0))
    lunch_time: time = Field(default_factory=lambda: time(12, 0))
    time_zone: str = "Europe/Warsaw"

    @field_validator("time_zone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if v not in pytz.all_timezones:
            return "Europe/Warsaw"
        return v

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Override model_dump() to serialize time objects to ISO format strings"""
        data = super().model_dump(*args, **kwargs)
        for field in [
            "wake_time",
            "sleep_time",
            "work_start_time",
            "work_end_time",
            "lunch_time",
        ]:
            if field in data and isinstance(data[field], time):
                data[field] = data[field].isoformat()
        return data

    @classmethod
    def parse_time(cls, time_str: str | time) -> time:
        """Parse ISO format time string back to time object"""
        if isinstance(time_str, time):
            return time_str
        return time.fromisoformat(str(time_str))


class UserActivity(Base):
    """Database model for tracking user activity"""

    __tablename__ = "user_activities"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("user_profiles.user_id"), nullable=False
    )
    interaction_type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    activity_metadata: Mapped[Dict | None] = mapped_column(
        JSON, nullable=True
    )  # Zmieniono z 'metadata' na 'activity_metadata'

    user: Mapped["UserProfile"] = relationship(
        f"{__name__}.UserProfile",
        back_populates="activities",
        lazy="selectin",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje obiekt UserActivity na słownik."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "interaction_type": self.interaction_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "activity_metadata": self.activity_metadata,
        }


class UserProfile(Base):
    """Database model for user profiles"""

    __tablename__ = "user_profiles"
    __table_args__ = {"extend_existing": True}

    user_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )
    preferences: Mapped[Dict] = mapped_column(
        JSON, nullable=False, default=lambda: UserPreferences().model_dump()
    )
    schedule: Mapped[Dict] = mapped_column(
        JSON, nullable=False, default=lambda: UserSchedule().model_dump()
    )
    topics_of_interest: Mapped[List[str]] = mapped_column(
        JSON, nullable=False, default=list
    )

    activities: Mapped[List["UserActivity"]] = relationship(
        f"{__name__}.UserActivity",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def get_preferences(self) -> UserPreferences:
        """Get user preferences as pydantic model"""
        return UserPreferences.model_validate(self.preferences)

    def get_schedule(self) -> UserSchedule:
        """Get user schedule as pydantic model"""
        if not self.schedule:
            return UserSchedule()

        # Handle case where schedule might be stored as serialized strings
        schedule_data = self.schedule.copy()
        for field in [
            "wake_time",
            "sleep_time",
            "work_start_time",
            "work_end_time",
            "lunch_time",
        ]:
            if field in schedule_data and schedule_data[field]:
                # Ensure the value is a string before parsing
                schedule_data[field] = UserSchedule.parse_time(
                    str(schedule_data[field])
                )

        return UserSchedule.model_validate(schedule_data)

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje obiekt UserProfile na słownik."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "preferences": self.preferences,
            "schedule": self.schedule,
            "topics_of_interest": self.topics_of_interest,
            "activities": [activity.to_dict() for activity in self.activities],
        }


class UserProfileData(BaseModel):
    """Pydantic model for user profile data"""

    user_id: str
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    schedule: UserSchedule = Field(default_factory=UserSchedule)
    topics_of_interest: List[str] = []
    activity_stats: Dict[str, int] = {}
    last_active: Optional[datetime] = None


# Create instance - will be initialized properly when database is available
profile_manager = None
