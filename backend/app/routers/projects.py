"""API endpoints for project management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.project_service import project_service


router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#6366f1"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


@router.post("")
async def create_project(data: ProjectCreate):
    """Create a new project."""
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Project name cannot be empty")

    return project_service.create(
        name=data.name.strip(),
        description=data.description,
        color=data.color
    )


@router.get("")
async def list_projects():
    """List all projects."""
    projects = project_service.list_all()
    return {"projects": projects}


@router.get("/{project_id}")
async def get_project(project_id: str, detailed: bool = False):
    """Get a project by ID."""
    if detailed:
        project = project_service.get_with_details(project_id)
    else:
        project = project_service.get(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.patch("/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate):
    """Update a project."""
    project = project_service.update(
        project_id,
        name=data.name,
        description=data.description,
        color=data.color
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its data."""
    result = project_service.delete(project_id)

    if not result:
        raise HTTPException(status_code=404, detail="Project not found")

    return result
