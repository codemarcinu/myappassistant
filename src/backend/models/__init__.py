import os

# Set User-Agent environment variable early to prevent warnings
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)

from .conversation import Conversation, Message
from .shopping import Product, ShoppingTrip
from .user_profile import UserActivity, UserProfile

__all__ = [
    "Conversation",
    "Message",
    "Product",
    "ShoppingTrip",
    "UserProfile",
    "UserActivity",
]
