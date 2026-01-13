"""Project service for CRUD operations."""

import uuid
import shutil
from datetime import datetime
from typing import Optional

from app.config import settings
from app.services.database import get_connection


class ProjectService:
    """Service for managing projects."""

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        color: str = "#6366f1"
    ) -> dict:
        """Create a new project."""
        project_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with get_connection() as conn:
            conn.execute(
                """INSERT INTO projects (id, name, description, color, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project_id, name, description, color, now, now)
            )

        # Create uploads directory for this project
        project_uploads = settings.data_dir / "uploads" / project_id
        project_uploads.mkdir(parents=True, exist_ok=True)

        return self.get(project_id)

    def list_all(self) -> list[dict]:
        """List all projects with document/chat counts."""
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT
                    p.*,
                    (SELECT COUNT(*) FROM documents WHERE project_id = p.id) as document_count,
                    (SELECT COUNT(*) FROM chats WHERE project_id = p.id) as chat_count
                FROM projects p
                ORDER BY p.updated_at DESC
            """).fetchall()

        return [dict(row) for row in rows]

    def get(self, project_id: str) -> Optional[dict]:
        """Get project with counts."""
        with get_connection() as conn:
            row = conn.execute("""
                SELECT
                    p.*,
                    (SELECT COUNT(*) FROM documents WHERE project_id = p.id) as document_count,
                    (SELECT COUNT(*) FROM chats WHERE project_id = p.id) as chat_count
                FROM projects p
                WHERE p.id = ?
            """, (project_id,)).fetchone()

        return dict(row) if row else None

    def get_with_details(self, project_id: str) -> Optional[dict]:
        """Get project with recent documents and chats."""
        project = self.get(project_id)
        if not project:
            return None

        with get_connection() as conn:
            # Get recent documents
            docs = conn.execute("""
                SELECT id, filename, page_count, uploaded_at
                FROM documents
                WHERE project_id = ?
                ORDER BY uploaded_at DESC
                LIMIT 5
            """, (project_id,)).fetchall()

            # Get recent chats
            chats = conn.execute("""
                SELECT c.id, c.title,
                       (SELECT COUNT(*) FROM chat_messages WHERE chat_id = c.id) as message_count,
                       c.updated_at
                FROM chats c
                WHERE c.project_id = ?
                ORDER BY c.updated_at DESC
                LIMIT 5
            """, (project_id,)).fetchall()

        project['recent_documents'] = [dict(d) for d in docs]
        project['recent_chats'] = [dict(c) for c in chats]

        return project

    def update(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None
    ) -> Optional[dict]:
        """Update project fields."""
        updates = {}
        if name is not None:
            updates['name'] = name
        if description is not None:
            updates['description'] = description
        if color is not None:
            updates['color'] = color

        if not updates:
            return self.get(project_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [datetime.utcnow().isoformat(), project_id]

        with get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE projects SET {set_clause}, updated_at = ? WHERE id = ?",
                values
            )
            if cursor.rowcount == 0:
                return None

        return self.get(project_id)

    def delete(self, project_id: str) -> Optional[dict]:
        """Delete project and all associated data."""
        project = self.get(project_id)
        if not project:
            return None

        doc_count = project['document_count']
        chat_count = project['chat_count']

        # Delete from database (CASCADE handles documents, chats, messages)
        with get_connection() as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))

        # Delete ChromaDB collection
        try:
            from app.services.vector_store import vector_store
            vector_store.delete_project_collection(project_id)
        except Exception:
            pass  # Collection might not exist

        # Delete uploaded files
        project_uploads = settings.data_dir / "uploads" / project_id
        if project_uploads.exists():
            shutil.rmtree(project_uploads)

        return {
            "status": "deleted",
            "id": project_id,
            "name": project['name'],
            "deleted_documents": doc_count,
            "deleted_chats": chat_count
        }


# Global instance
project_service = ProjectService()
