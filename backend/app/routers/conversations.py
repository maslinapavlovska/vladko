"""API endpoints for conversation management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.conversation_service import conversation_service

router = APIRouter()


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: str


@router.get("")
async def list_conversations(page: int = 1, per_page: int = 20):
    """List all conversations with pagination."""
    return conversation_service.list_conversations(page=page, per_page=per_page)


@router.post("")
async def create_conversation(data: ConversationCreate = None):
    """Create a new conversation."""
    title = data.title if data else None
    return conversation_service.create_conversation(title=title)


@router.get("/search")
async def search_conversations(q: str, limit: int = 20):
    """Search conversations by message content."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    return conversation_service.search_conversations(query=q, limit=limit)


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a conversation with all its messages."""
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.patch("/{conversation_id}")
async def update_conversation(conversation_id: str, data: ConversationUpdate):
    """Update conversation title."""
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    conversation = conversation_service.update_conversation(conversation_id, data.title)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    deleted = conversation_service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "id": conversation_id}
