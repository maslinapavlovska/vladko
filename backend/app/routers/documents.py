"""API endpoints for document management."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pathlib import Path
import shutil

from app.config import settings
from app.services.pdf_service import extract_and_chunk_pdf
from app.services.vector_store import vector_store
from app.services.document_service import document_service
from app.services.project_service import project_service

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Query(..., description="Project ID to upload document to")
):
    """Upload and process a PDF document to a project."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Verify project exists
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if document already exists in this project
    existing = document_service.get_by_filename(project_id, file.filename)
    if existing:
        raise HTTPException(status_code=409, detail="Document with this name already exists in project")

    # Save the file to project-specific directory
    project_uploads = settings.data_dir / "uploads" / project_id
    project_uploads.mkdir(parents=True, exist_ok=True)
    file_path = project_uploads / file.filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Get file size
    file_size = file_path.stat().st_size

    # Extract and chunk the PDF
    try:
        chunks = extract_and_chunk_pdf(file_path)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {str(e)}")

    if not chunks:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Could not extract any text from PDF")

    # Count pages
    pages = set(chunk["page"] for chunk in chunks)

    # Create document record in database
    try:
        document = document_service.create(
            project_id=project_id,
            filename=file.filename,
            filepath=str(file_path),
            file_size=file_size,
            page_count=len(pages),
            chunk_count=len(chunks)
        )
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to create document record: {str(e)}")

    # Store chunks in project's vector collection
    try:
        await vector_store.add_chunks(
            file.filename,
            chunks,
            project_id=project_id,
            document_id=document["id"]
        )
    except Exception as e:
        file_path.unlink(missing_ok=True)
        document_service.delete(document["id"])
        raise HTTPException(status_code=500, detail=f"Failed to store document: {str(e)}")

    return {
        "id": document["id"],
        "filename": file.filename,
        "project_id": project_id,
        "pages": len(pages),
        "chunks": len(chunks),
        "file_size": file_size,
    }


@router.get("")
async def list_documents(
    project_id: str = Query(..., description="Project ID to list documents from")
):
    """List all documents in a project."""
    # Verify project exists
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    documents = document_service.list_by_project(project_id)
    return {"documents": documents}


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get a specific document by ID."""
    document = document_service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a specific document."""
    document = document_service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    project_id = document["project_id"]
    filename = document["filename"]

    # Remove from vector store
    try:
        vector_store.delete_document(filename, project_id=project_id)
    except Exception:
        pass  # Continue even if vector deletion fails

    # Remove file
    file_path = Path(document["filepath"])
    file_path.unlink(missing_ok=True)

    # Remove from database
    document_service.delete(document_id)

    return {
        "status": "deleted",
        "id": document_id,
        "filename": filename,
        "project_id": project_id
    }
