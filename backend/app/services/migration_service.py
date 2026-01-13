"""Migration service for transitioning existing data to project-based structure."""

import sqlite3
import shutil
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.services.database import get_connection, init_database


def migrate_legacy_data() -> dict:
    """
    Migrate existing data from old structure to new project-based structure.

    - Creates a "Legacy" project
    - Migrates conversations from conversations.db to chats table
    - Migrates documents from uploads/ to project uploads
    - Copies ChromaDB vectors to project collection

    Returns migration stats.
    """
    stats = {
        "conversations_migrated": 0,
        "messages_migrated": 0,
        "documents_migrated": 0,
        "errors": []
    }

    # Check if migration is needed
    old_db = settings.data_dir / "conversations.db"
    marker_file = settings.data_dir / ".migration_complete"

    if marker_file.exists():
        return {"status": "already_migrated"}

    # Initialize new database if needed
    init_database()

    # Create Legacy project for existing data
    legacy_project_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO projects (id, name, description, color, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (legacy_project_id, "Legacy Data", "Migrated data from previous version", "#64748b", now, now)
        )

    # Migrate conversations if old database exists
    if old_db.exists():
        stats.update(_migrate_conversations(old_db, legacy_project_id))

    # Migrate documents from old uploads directory
    stats.update(_migrate_documents(legacy_project_id))

    # Migrate ChromaDB vectors
    stats.update(_migrate_vectors(legacy_project_id))

    # Mark migration as complete
    marker_file.touch()

    stats["status"] = "completed"
    stats["project_id"] = legacy_project_id

    return stats


def _migrate_conversations(old_db: Path, project_id: str) -> dict:
    """Migrate conversations from old database to new chats table."""
    stats = {"conversations_migrated": 0, "messages_migrated": 0, "errors": []}

    try:
        old_conn = sqlite3.connect(str(old_db))
        old_conn.row_factory = sqlite3.Row

        # Get all conversations
        conversations = old_conn.execute(
            "SELECT * FROM conversations ORDER BY created_at ASC"
        ).fetchall()

        for conv in conversations:
            try:
                # Insert chat
                with get_connection() as conn:
                    conn.execute(
                        """INSERT INTO chats (id, project_id, title, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (conv["id"], project_id, conv["title"], conv["created_at"], conv["updated_at"])
                    )

                # Get messages for this conversation
                messages = old_conn.execute(
                    "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                    (conv["id"],)
                ).fetchall()

                for msg in messages:
                    with get_connection() as conn:
                        conn.execute(
                            """INSERT INTO chat_messages (id, chat_id, role, content, citations, reasoning, created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (msg["id"], msg["conversation_id"], msg["role"], msg["content"],
                             msg["citations"], msg["reasoning"], msg["created_at"])
                        )
                    stats["messages_migrated"] += 1

                stats["conversations_migrated"] += 1

            except Exception as e:
                stats["errors"].append(f"Error migrating conversation {conv['id']}: {str(e)}")

        old_conn.close()

    except Exception as e:
        stats["errors"].append(f"Error accessing old database: {str(e)}")

    return stats


def _migrate_documents(project_id: str) -> dict:
    """Migrate documents from old uploads directory to project structure."""
    stats = {"documents_migrated": 0, "errors": []}

    old_uploads = settings.upload_dir
    if not old_uploads.exists():
        return stats

    # Create project uploads directory
    project_uploads = settings.data_dir / "uploads" / project_id
    project_uploads.mkdir(parents=True, exist_ok=True)

    # Get all PDF files from old uploads
    pdf_files = list(old_uploads.glob("*.pdf"))

    for pdf_file in pdf_files:
        try:
            # Copy file to project directory
            new_path = project_uploads / pdf_file.name
            shutil.copy2(pdf_file, new_path)

            # Create document record
            document_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            file_size = new_path.stat().st_size

            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO documents (id, project_id, filename, filepath, file_size, uploaded_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (document_id, project_id, pdf_file.name, str(new_path), file_size, now)
                )

            stats["documents_migrated"] += 1

        except Exception as e:
            stats["errors"].append(f"Error migrating document {pdf_file.name}: {str(e)}")

    return stats


def _migrate_vectors(project_id: str) -> dict:
    """Copy vectors from legacy collection to project collection."""
    stats = {"vectors_migrated": 0, "errors": []}

    try:
        from app.services.vector_store import vector_store

        # Get all data from legacy collection
        legacy_data = vector_store.collection.get(
            include=["documents", "metadatas", "embeddings"]
        )

        if not legacy_data.get("ids"):
            return stats

        # Get or create project collection
        project_collection = vector_store.get_project_collection(project_id)

        # Add all vectors to project collection
        if legacy_data["ids"]:
            project_collection.add(
                ids=[f"migrated_{id}" for id in legacy_data["ids"]],
                embeddings=legacy_data["embeddings"],
                documents=legacy_data["documents"],
                metadatas=legacy_data["metadatas"]
            )
            stats["vectors_migrated"] = len(legacy_data["ids"])

    except Exception as e:
        stats["errors"].append(f"Error migrating vectors: {str(e)}")

    return stats


def check_migration_status() -> dict:
    """Check current migration status."""
    marker_file = settings.data_dir / ".migration_complete"
    old_db = settings.data_dir / "conversations.db"

    if marker_file.exists():
        return {"status": "completed"}
    elif old_db.exists():
        return {"status": "pending", "has_legacy_data": True}
    else:
        return {"status": "not_needed", "has_legacy_data": False}
