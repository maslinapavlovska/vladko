from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, documents, query

app = FastAPI(
    title="RAG Document Q&A API",
    description="Upload PDFs and query them with natural language",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(query.router, tags=["Query"])
