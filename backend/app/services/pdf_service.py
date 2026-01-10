import fitz  # PyMuPDF
from pathlib import Path

from app.config import settings


def extract_and_chunk_pdf(file_path: Path) -> list[dict]:
    """
    Extract text from PDF and split into chunks with metadata.

    Returns a list of chunks, each containing:
    - text: The chunk content
    - page: The 1-indexed page number
    - chunk_id: Unique identifier for the chunk
    """
    chunks = []

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Could not open PDF: {str(e)}")

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        if not text.strip():
            continue

        # Chunk this page's text
        page_chunks = chunk_text(
            text=text,
            page=page_num + 1,  # 1-indexed
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        chunks.extend(page_chunks)

    doc.close()
    return chunks


def chunk_text(text: str, page: int, chunk_size: int, overlap: int) -> list[dict]:
    """
    Split text into overlapping chunks.

    Attempts to break at sentence boundaries when possible.
    """
    chunks = []
    text = text.strip()

    if not text:
        return chunks

    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size

        # If we're not at the end, try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings in the last portion of the chunk
            chunk_text = text[start:end]
            last_period = chunk_text.rfind(". ")
            last_newline = chunk_text.rfind("\n")

            # Use the latest sentence boundary if it's in the back half of the chunk
            boundary = max(last_period, last_newline)
            if boundary > chunk_size // 2:
                end = start + boundary + 1

        chunk_content = text[start:end].strip()

        if chunk_content:
            chunks.append({
                "text": chunk_content,
                "page": page,
                "chunk_id": chunk_index,
            })
            chunk_index += 1

        # Move start position with overlap
        start = end - overlap if end < len(text) else len(text)

    return chunks
