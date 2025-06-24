from __future__ import annotations

"""
Models package - unified Base class to prevent SQLAlchemy Multiple Classes conflicts.
Import models directly from their modules instead of from this package.
"""

# Import the unified Base class from core.database
from backend.core.database import Base

# Export Base for use in all models
__all__ = ["Base"]

# Note: Individual models should be imported directly from their modules:
# from backend.models.conversation import Conversation, Message
# from backend.models.shopping import ShoppingTrip, Product
# from backend.models.user_profile import UserProfile, UserActivity
# from backend.auth.models import User, Role, UserRole
