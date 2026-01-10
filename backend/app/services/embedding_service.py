import httpx

from app.config import settings


async def get_embedding(text: str) -> list[float]:
    """
    Generate embedding for text using Ollama.

    Returns a list of floats representing the embedding vector.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.ollama_host}/api/embeddings",
            json={
                "model": settings.embedding_model,
                "prompt": text,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.

    Processes sequentially to avoid overwhelming the Ollama server.
    """
    embeddings = []
    for text in texts:
        embedding = await get_embedding(text)
        embeddings.append(embedding)
    return embeddings
