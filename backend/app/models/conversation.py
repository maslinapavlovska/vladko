"""Pydantic models for conversations and messages."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


class MessageBase(BaseModel):
    role: Literal["user", "assistant", "error"]
    content: str


class MessageCreate(MessageBase):
    citations: Optional[list] = None
    reasoning: Optional[dict] = None


class Message(MessageBase):
    id: str = Field(default_factory=generate_uuid)
    conversation_id: str
    citations: Optional[list] = None
    reasoning: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None  # Auto-generated if not provided


class ConversationUpdate(BaseModel):
    title: str


class Conversation(ConversationBase):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: Optional[int] = None
    preview: Optional[str] = None


class ConversationDetail(Conversation):
    messages: list[Message] = []


class ConversationList(BaseModel):
    conversations: list[Conversation]
    total: int
    page: int
    per_page: int
