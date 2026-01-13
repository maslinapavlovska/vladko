"""Database service for project-based organization."""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from app.config import settings


DATABASE_PATH = settings.data_dir / "vladko.db"


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(str(DATABASE_PATH))
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


def init_database():
    """Initialize database schema on startup."""
    with get_connection() as conn:
        conn.executescript("""
            -- Projects table
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#6366f1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Documents table
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_size INTEGER,
                page_count INTEGER,
                chunk_count INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                UNIQUE(project_id, filename)
            );

            -- Chats table
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            -- Messages table
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'error')),
                content TEXT NOT NULL,
                citations JSON,
                reasoning JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            );

            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project_id);
            CREATE INDEX IF NOT EXISTS idx_chats_project ON chats(project_id);
            CREATE INDEX IF NOT EXISTS idx_chats_updated ON chats(updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_chat ON chat_messages(chat_id, created_at);
        """)

        # Create triggers for updating timestamps
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_chat_timestamp
                AFTER INSERT ON chat_messages
            BEGIN
                UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.chat_id;
            END;
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_project_timestamp_docs
                AFTER INSERT ON documents
            BEGIN
                UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.project_id;
            END;
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_project_timestamp_chats
                AFTER INSERT ON chats
            BEGIN
                UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.project_id;
            END;
        """)


def check_migration_needed() -> bool:
    """Check if migration from old conversations.db is needed."""
    old_db = settings.data_dir / "conversations.db"
    marker_file = settings.data_dir / ".migration_complete"

    # Migration needed if old DB exists and migration not complete
    return old_db.exists() and not marker_file.exists()


def is_new_install() -> bool:
    """Check if this is a fresh install (no existing data)."""
    old_db = settings.data_dir / "conversations.db"
    new_db = DATABASE_PATH

    return not old_db.exists() and not new_db.exists()
