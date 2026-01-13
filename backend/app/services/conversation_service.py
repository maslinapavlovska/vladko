"""SQLite-based conversation storage service."""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from app.config import settings


class ConversationService:
    def __init__(self):
        self.db_path = settings.data_dir / "conversations.db"
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'error')),
                    content TEXT NOT NULL,
                    citations JSON,
                    reasoning JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages(conversation_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_conversations_updated
                    ON conversations(updated_at DESC);
            """)

            # Create trigger for updating conversation timestamp
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS update_conversation_timestamp
                    AFTER INSERT ON messages
                BEGIN
                    UPDATE conversations
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = NEW.conversation_id;
                END;
            """)

    # ==================== Conversation CRUD ====================

    def create_conversation(self, title: Optional[str] = None) -> dict:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        title = title or "New Conversation"
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conversation_id, title, now, now)
            )

        return {
            "id": conversation_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "preview": None
        }

    def list_conversations(self, page: int = 1, per_page: int = 20) -> dict:
        """List all conversations with pagination."""
        offset = (page - 1) * per_page

        with self._get_connection() as conn:
            # Get total count
            total = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]

            # Get conversations with message count and preview
            rows = conn.execute("""
                SELECT
                    c.id,
                    c.title,
                    c.created_at,
                    c.updated_at,
                    COUNT(m.id) as message_count,
                    (SELECT content FROM messages
                     WHERE conversation_id = c.id AND role = 'user'
                     ORDER BY created_at ASC LIMIT 1) as preview
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset)).fetchall()

        conversations = []
        for row in rows:
            preview = row["preview"]
            if preview and len(preview) > 50:
                preview = preview[:50].rsplit(' ', 1)[0] + "..."

            conversations.append({
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "message_count": row["message_count"],
                "preview": preview
            })

        return {
            "conversations": conversations,
            "total": total,
            "page": page,
            "per_page": per_page
        }

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get a conversation with all its messages."""
        with self._get_connection() as conn:
            # Get conversation
            conv_row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,)
            ).fetchone()

            if not conv_row:
                return None

            # Get messages
            msg_rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                (conversation_id,)
            ).fetchall()

        messages = []
        for row in msg_rows:
            messages.append({
                "id": row["id"],
                "conversation_id": row["conversation_id"],
                "role": row["role"],
                "content": row["content"],
                "citations": json.loads(row["citations"]) if row["citations"] else None,
                "reasoning": json.loads(row["reasoning"]) if row["reasoning"] else None,
                "created_at": row["created_at"]
            })

        return {
            "id": conv_row["id"],
            "title": conv_row["title"],
            "created_at": conv_row["created_at"],
            "updated_at": conv_row["updated_at"],
            "messages": messages
        }

    def update_conversation(self, conversation_id: str, title: str) -> Optional[dict]:
        """Update conversation title."""
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, conversation_id)
            )

            if cursor.rowcount == 0:
                return None

            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,)
            ).fetchone()

        return {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            return cursor.rowcount > 0

    # ==================== Message Operations ====================

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: Optional[list] = None,
        reasoning: Optional[dict] = None
    ) -> dict:
        """Add a message to a conversation."""
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO messages
                   (id, conversation_id, role, content, citations, reasoning, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    message_id,
                    conversation_id,
                    role,
                    content,
                    json.dumps(citations) if citations else None,
                    json.dumps(reasoning) if reasoning else None,
                    now
                )
            )

        return {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "citations": citations,
            "reasoning": reasoning,
            "created_at": now
        }

    def get_recent_messages(
        self,
        conversation_id: str,
        max_turns: int = 5
    ) -> list[dict]:
        """Get recent messages for context (last N turns = N*2 messages)."""
        limit = max_turns * 2

        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM messages
                   WHERE conversation_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (conversation_id, limit)
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

    def search_conversations(self, query: str, limit: int = 20) -> list[dict]:
        """Full-text search across messages (case-insensitive for all languages)."""
        query_lower = query.lower()

        with self._get_connection() as conn:
            # Fetch all messages and filter in Python for proper Unicode case-insensitive search
            rows = conn.execute(
                """SELECT c.id, c.title, c.created_at, c.updated_at,
                          m.content as matched_content
                   FROM conversations c
                   JOIN messages m ON c.id = m.conversation_id
                   ORDER BY c.updated_at DESC"""
            ).fetchall()

        # Filter and deduplicate in Python for proper Unicode handling
        seen_ids = set()
        results = []
        for row in rows:
            conv_id = row["id"]
            if conv_id in seen_ids:
                continue

            content_lower = row["matched_content"].lower()
            title_lower = row["title"].lower()

            if query_lower in content_lower or query_lower in title_lower:
                seen_ids.add(conv_id)
                matched = row["matched_content"]
                results.append({
                    "id": conv_id,
                    "title": row["title"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "matched_content": matched[:100] + "..." if len(matched) > 100 else matched
                })

            if len(results) >= limit:
                break

        return results

    def update_conversation_title_from_message(self, conversation_id: str, first_message: str):
        """Auto-generate title from first message."""
        # Take first 50 chars, cut at word boundary
        truncated = first_message[:50]
        if len(first_message) > 50:
            last_space = truncated.rfind(' ')
            if last_space > 20:
                truncated = truncated[:last_space]
            truncated += "..."

        self.update_conversation(conversation_id, truncated)


# Global instance
conversation_service = ConversationService()
