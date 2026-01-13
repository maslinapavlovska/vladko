from fastapi import APIRouter, HTTPException
import httpx

from app.config import settings
from app.services.migration_service import migrate_legacy_data, check_migration_status

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check API and Ollama server status."""
    ollama_status = "unreachable"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_host}/api/tags")
            if response.status_code == 200:
                ollama_status = "ok"
    except Exception:
        pass

    return {
        "api": "ok",
        "ollama": ollama_status,
        "ollama_host": settings.ollama_host,
    }


@router.get("/migration/status")
async def get_migration_status():
    """Check migration status."""
    return check_migration_status()


@router.post("/migration/run")
async def run_migration():
    """Manually trigger migration of legacy data."""
    status = check_migration_status()
    if status.get("status") == "completed":
        return {"status": "already_migrated", "message": "Migration was already completed"}

    try:
        result = migrate_legacy_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")
