"""
Module containing user activity related functions.
"""

import logging
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user_profile import InteractionType, UserActivity

logger = logging.getLogger(__name__)


async def create_user_activity(
    db: AsyncSession,
    user_id: str,
    interaction_type: InteractionType,
    content: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> UserActivity:
    """
    Creates a new user activity record in the database.

    Args:
        db: Database session
        user_id: ID of the user
        interaction_type: Type of interaction
        content: Optional content of the interaction
        metadata: Optional metadata for the interaction

    Returns:
        The created UserActivity instance
    """
    try:
        # Create the activity with activity_metadata instead of metadata (original field name)
        activity = UserActivity(
            user_id=user_id,
            interaction_type=(
                interaction_type.value
                if isinstance(interaction_type, InteractionType)
                else interaction_type
            ),
            content=content,
            activity_metadata=metadata,  # Use the renamed field
        )

        db.add(activity)
        await db.commit()
        await db.refresh(activity)

        logger.info(
            f"Created activity record for user {user_id}, type: {interaction_type}"
        )
        return activity

    except Exception as e:
        logger.error(f"Error creating user activity: {e}")
        await db.rollback()
        raise
