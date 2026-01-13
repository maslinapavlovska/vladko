"""Document service for CRUD operations."""

import uuid
from datetime import datetime
from typing import Optional

from app.services.database import get_connection


class DocumentService:
    """Service for managing documents within projects."""

    def create(
        self,
        project_id: str,
        filename: str,
        filepath: str,
        file_size: int = None,
        page_count: int = None,
        chunk_count: int = None
    ) -> dict:
        """Create a new document record."""
        document_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with get_connection() as conn:
            conn.execute(
                """INSERT INTO documents (id, project_id, filename, filepath, file_size, page_count, chunk_count, uploaded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (document_id, project_id, filename, filepath, file_size, page_count, chunk_count, now)
            )

        return self.get(document_id)

    def get(self, document_id: str) -> Optional[dict]:
        """Get a document by ID."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,)
            ).fetchone()

        return dict(row) if row else None

    def get_by_filename(self, project_id: str, filename: str) -> Optional[dict]:
        """Get a document by project and filename."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE project_id = ? AND filename = ?",
                (project_id, filename)
            ).fetchone()

        return dict(row) if row else None

    def list_by_project(self, project_id: str) -> list[dict]:
        """List all documents in a project."""
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM documents
                   WHERE project_id = ?
                   ORDER BY uploaded_at DESC""",
                (project_id,)
            ).fetchall()

        return [dict(row) for row in rows]

    def delete(self, document_id: str) -> bool:
        """Delete a document by ID."""
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE id = ?",
                (document_id,)
            )
            return cursor.rowcount > 0

    def delete_by_filename(self, project_id: str, filename: str) -> bool:
        """Delete a document by project and filename."""
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE project_id = ? AND filename = ?",
                (project_id, filename)
            )
            return cursor.rowcount > 0


# Global instance
document_service = DocumentService()
