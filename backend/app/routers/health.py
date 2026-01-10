from fastapi import APIRouter
import httpx

from app.config import settings

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
