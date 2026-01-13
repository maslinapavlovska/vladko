"""API endpoints for chat/conversation management."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.chat_service import chat_service
from app.services.project_service import project_service

router = APIRouter()


class ChatCreate(BaseModel):
    title: Optional[str] = None


class ChatUpdate(BaseModel):
    title: str


@router.get("")
async def list_chats(
    project_id: str = Query(..., description="Project ID to list chats from"),
    page: int = 1,
    per_page: int = 20
):
    """List all chats in a project with pagination."""
    # Verify project exists
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return chat_service.list_chats(project_id, page=page, per_page=per_page)


@router.post("")
async def create_chat(
    project_id: str = Query(..., description="Project ID to create chat in"),
    data: ChatCreate = None
):
    """Create a new chat in a project."""
    # Verify project exists
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    title = data.title if data else None
    return chat_service.create_chat(project_id, title=title)


@router.get("/search")
async def search_chats(
    project_id: str = Query(..., description="Project ID to search in"),
    q: str = Query(..., description="Search query"),
    limit: int = 20
):
    """Search chats by message content within a project."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    # Verify project exists
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return chat_service.search_chats(project_id, query=q, limit=limit)


@router.get("/{chat_id}")
async def get_chat(chat_id: str):
    """Get a chat with all its messages."""
    chat = chat_service.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/{chat_id}")
async def update_chat(chat_id: str, data: ChatUpdate):
    """Update chat title."""
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    chat = chat_service.update_chat(chat_id, data.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat and all its messages."""
    deleted = chat_service.delete_chat(chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "deleted", "id": chat_id}
