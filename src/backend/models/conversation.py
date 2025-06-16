from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import deferred, relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = deferred(
        Column(String, nullable=False)
    )  # Large text, load only when needed
    role = Column(String, nullable=False, index=True)  # "user" or "assistant"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    conversation = relationship(
        "Conversation", back_populates="messages", lazy="selectin"
    )


# Composite index for common message queries
Index("ix_message_conversation_created", Message.conversation_id, Message.created_at)
