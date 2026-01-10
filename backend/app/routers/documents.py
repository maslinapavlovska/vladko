from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil

from app.config import settings
from app.services.pdf_service import extract_and_chunk_pdf
from app.services.vector_store import vector_store

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a PDF document."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save the file
    file_path = settings.upload_dir / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Extract and chunk the PDF
    try:
        chunks = extract_and_chunk_pdf(file_path)
    except Exception as e:
        # Clean up the file if extraction fails
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {str(e)}")

    if not chunks:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Could not extract any text from PDF")

    # Store chunks in vector database
    try:
        await vector_store.add_chunks(file.filename, chunks)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to store document: {str(e)}")

    # Count pages
    pages = set(chunk["page"] for chunk in chunks)

    return {
        "filename": file.filename,
        "pages": len(pages),
        "chunks": len(chunks),
    }


@router.get("")
async def list_documents():
    """List all uploaded documents."""
    files = []
    for file_path in settings.upload_dir.glob("*.pdf"):
        files.append(file_path.name)
    return files


@router.delete("/{filename}")
async def delete_document(filename: str):
    """Delete a specific document."""
    file_path = settings.upload_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from vector store
    try:
        vector_store.delete_document(filename)
    except Exception:
        pass  # Continue even if vector deletion fails

    # Remove file
    file_path.unlink(missing_ok=True)

    return {"status": "deleted", "filename": filename}
