"""Chat service for project-based conversations."""

import json
import uuid
from datetime import datetime
from typing import Optional

from app.services.database import get_connection


class ChatService:
    """Service for managing chats within projects."""

    # ==================== Chat CRUD ====================

    def create_chat(self, project_id: str, title: Optional[str] = None) -> dict:
        """Create a new chat in a project."""
        chat_id = str(uuid.uuid4())
        title = title or "New Chat"
        now = datetime.utcnow().isoformat()

        with get_connection() as conn:
            conn.execute(
                """INSERT INTO chats (id, project_id, title, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (chat_id, project_id, title, now, now)
            )

        return {
            "id": chat_id,
            "project_id": project_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "preview": None
        }

    def list_chats(self, project_id: str, page: int = 1, per_page: int = 20) -> dict:
        """List all chats in a project with pagination."""
        offset = (page - 1) * per_page

        with get_connection() as conn:
            # Get total count for this project
            total = conn.execute(
                "SELECT COUNT(*) FROM chats WHERE project_id = ?",
                (project_id,)
            ).fetchone()[0]

            # Get chats with message count and preview
            rows = conn.execute("""
                SELECT
                    c.id,
                    c.project_id,
                    c.title,
                    c.created_at,
                    c.updated_at,
                    COUNT(m.id) as message_count,
                    (SELECT content FROM chat_messages
                     WHERE chat_id = c.id AND role = 'user'
                     ORDER BY created_at ASC LIMIT 1) as preview
                FROM chats c
                LEFT JOIN chat_messages m ON c.id = m.chat_id
                WHERE c.project_id = ?
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ? OFFSET ?
            """, (project_id, per_page, offset)).fetchall()

        chats = []
        for row in rows:
            preview = row["preview"]
            if preview and len(preview) > 50:
                preview = preview[:50].rsplit(' ', 1)[0] + "..."

            chats.append({
                "id": row["id"],
                "project_id": row["project_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "message_count": row["message_count"],
                "preview": preview
            })

        return {
            "chats": chats,
            "total": total,
            "page": page,
            "per_page": per_page
        }

    def get_chat(self, chat_id: str) -> Optional[dict]:
        """Get a chat with all its messages."""
        with get_connection() as conn:
            # Get chat
            chat_row = conn.execute(
                "SELECT * FROM chats WHERE id = ?",
                (chat_id,)
            ).fetchone()

            if not chat_row:
                return None

            # Get messages
            msg_rows = conn.execute(
                "SELECT * FROM chat_messages WHERE chat_id = ? ORDER BY created_at ASC",
                (chat_id,)
            ).fetchall()

        messages = []
        for row in msg_rows:
            messages.append({
                "id": row["id"],
                "chat_id": row["chat_id"],
                "role": row["role"],
                "content": row["content"],
                "citations": json.loads(row["citations"]) if row["citations"] else None,
                "reasoning": json.loads(row["reasoning"]) if row["reasoning"] else None,
                "created_at": row["created_at"]
            })

        return {
            "id": chat_row["id"],
            "project_id": chat_row["project_id"],
            "title": chat_row["title"],
            "created_at": chat_row["created_at"],
            "updated_at": chat_row["updated_at"],
            "messages": messages
        }

    def update_chat(self, chat_id: str, title: str) -> Optional[dict]:
        """Update chat title."""
        now = datetime.utcnow().isoformat()

        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, chat_id)
            )

            if cursor.rowcount == 0:
                return None

            row = conn.execute(
                "SELECT * FROM chats WHERE id = ?",
                (chat_id,)
            ).fetchone()

        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat and all its messages."""
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM chats WHERE id = ?",
                (chat_id,)
            )
            return cursor.rowcount > 0

    # ==================== Message Operations ====================

    def add_message(
        self,
        chat_id: str,
        role: str,
        content: str,
        citations: Optional[list] = None,
        reasoning: Optional[dict] = None
    ) -> dict:
        """Add a message to a chat."""
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with get_connection() as conn:
            conn.execute(
                """INSERT INTO chat_messages
                   (id, chat_id, role, content, citations, reasoning, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    message_id,
                    chat_id,
                    role,
                    content,
                    json.dumps(citations) if citations else None,
                    json.dumps(reasoning) if reasoning else None,
                    now
                )
            )

        return {
            "id": message_id,
            "chat_id": chat_id,
            "role": role,
            "content": content,
            "citations": citations,
            "reasoning": reasoning,
            "created_at": now
        }

    def get_recent_messages(self, chat_id: str, max_turns: int = 5) -> list[dict]:
        """Get recent messages for context (last N turns = N*2 messages)."""
        limit = max_turns * 2

        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM chat_messages
                   WHERE chat_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (chat_id, limit)
            ).fetchall()

        # Reverse to get chronological order
        messages = []
        for row in reversed(rows):
            messages.append({
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"]
            })

        return messages

    def search_chats(self, project_id: str, query: str, limit: int = 20) -> list[dict]:
        """Full-text search across messages in a project (case-insensitive for all languages)."""
        query_lower = query.lower()

        with get_connection() as conn:
            # Fetch all messages for the project and filter in Python for proper Unicode handling
            rows = conn.execute(
                """SELECT c.id, c.title, c.created_at, c.updated_at,
                          m.content as matched_content
                   FROM chats c
                   JOIN chat_messages m ON c.id = m.chat_id
                   WHERE c.project_id = ?
                   ORDER BY c.updated_at DESC""",
                (project_id,)
            ).fetchall()

        # Filter and deduplicate in Python for proper Unicode handling
        seen_ids = set()
        results = []
        for row in rows:
            chat_id = row["id"]
            if chat_id in seen_ids:
                continue

            content_lower = row["matched_content"].lower()
            title_lower = row["title"].lower()

            if query_lower in content_lower or query_lower in title_lower:
                seen_ids.add(chat_id)
                matched = row["matched_content"]
                results.append({
                    "id": chat_id,
                    "title": row["title"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "matched_content": matched[:100] + "..." if len(matched) > 100 else matched
                })

            if len(results) >= limit:
                break

        return results

    def update_chat_title_from_message(self, chat_id: str, first_message: str):
        """Auto-generate title from first message."""
        # Take first 50 chars, cut at word boundary
        truncated = first_message[:50]
        if len(first_message) > 50:
            last_space = truncated.rfind(' ')
            if last_space > 20:
                truncated = truncated[:last_space]
            truncated += "..."

        self.update_chat(chat_id, truncated)

    def get_chat_project_id(self, chat_id: str) -> Optional[str]:
        """Get the project ID for a chat."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT project_id FROM chats WHERE id = ?",
                (chat_id,)
            ).fetchone()

        return row["project_id"] if row else None


# Global instance
chat_service = ChatService()
