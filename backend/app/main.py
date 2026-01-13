from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, documents, query, conversations, projects
from app.services.database import init_database, check_migration_needed
from app.services.migration_service import migrate_legacy_data, check_migration_status

app = FastAPI(
    title="Vladko API",
    description="Project-based document Q&A with RAG",
    version="2.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup and run migration if needed."""
    init_database()

    # Auto-migrate legacy data if present
    if check_migration_needed():
        try:
            result = migrate_legacy_data()
            print(f"Migration completed: {result}")
        except Exception as e:
            print(f"Migration failed: {e}")


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(query.router, tags=["Query"])
app.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
