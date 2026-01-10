from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from app.config import settings
from app.services.vector_store import vector_store
from app.services.llm_service import (
    generate_answer,
    analyze_mcq_question,
    reason_over_evidence,
)

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class Citation(BaseModel):
    filename: str
    page: int
    excerpt: str
    match_type: str
    keyword_matches: list[str]
    scores: dict[str, float]


class RetrievalSummary(BaseModel):
    source: str
    match_type: str
    keywords_found: list[str]
    scores: dict[str, float]


class Stage1Analysis(BaseModel):
    """Stage 1: LLM query analysis results."""
    search_terms: list[str]
    reasoning: str
    raw_response: Optional[str] = None


class GrepResult(BaseModel):
    """Stage 2: Grep search result with context."""
    term: str
    filename: str
    page: int
    match_line: str
    context_before: list[str]
    context_after: list[str]
    full_excerpt: str


class Reasoning(BaseModel):
    # Original fields (for non-MCQ questions)
    keywords_extracted: list[str] = []
    chunks_retrieved: int = 0
    retrieval_summary: list[RetrievalSummary] = []
    prompt_sent: str = ""
    is_mcq: bool = False
    mcq_options: list[str] = []
    # New two-stage MCQ fields
    stage1_analysis: Optional[Stage1Analysis] = None
    stage2_grep_results: Optional[list[GrepResult]] = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    reasoning: Reasoning


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents with hybrid search and reasoning transparency."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Detect if this is an MCQ question
    is_mcq, mcq_options = vector_store._detect_mcq_options(request.question)

    if is_mcq and mcq_options:
        # ===== TWO-STAGE MCQ PIPELINE =====
        return await _handle_mcq_query(request.question, mcq_options)
    else:
        # ===== STANDARD HYBRID SEARCH PIPELINE =====
        return await _handle_standard_query(request)


async def _handle_mcq_query(question: str, mcq_options: list[str]) -> QueryResponse:
    """Handle MCQ questions with two-stage LLM pipeline."""

    # Stage 1: LLM analyzes question to determine search terms
    try:
        analysis = await analyze_mcq_question(question, mcq_options)
        search_terms = analysis.get("search_terms", mcq_options)
    except Exception as e:
        # Fallback: use options as search terms
        analysis = {
            "search_terms": mcq_options,
            "reasoning": f"Fallback due to error: {str(e)}",
        }
        search_terms = mcq_options

    # Stage 2: Grep search with context
    grep_results = vector_store.grep_search(search_terms, context_lines=3)

    # Stage 3: LLM reasons over evidence
    try:
        answer, prompt_sent = await reason_over_evidence(question, mcq_options, grep_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    # Format citations from grep results
    citations = []
    seen = set()  # Avoid duplicate citations
    for result in grep_results[:10]:  # Limit citations
        key = (result["filename"], result["page"], result["term"])
        if key not in seen:
            seen.add(key)
            citations.append(
                Citation(
                    filename=result["filename"],
                    page=result["page"],
                    excerpt=result["full_excerpt"][:300] + "..." if len(result["full_excerpt"]) > 300 else result["full_excerpt"],
                    match_type="grep",
                    keyword_matches=[result["term"]],
                    scores={"grep_match": 1.0, "keyword": 0.0, "semantic": 0.0},
                )
            )

    # Build reasoning with two-stage info
    reasoning = Reasoning(
        is_mcq=True,
        mcq_options=mcq_options,
        prompt_sent=prompt_sent,
        stage1_analysis=Stage1Analysis(
            search_terms=analysis.get("search_terms", []),
            reasoning=analysis.get("reasoning", ""),
            raw_response=analysis.get("raw_response"),
        ),
        stage2_grep_results=[
            GrepResult(
                term=r["term"],
                filename=r["filename"],
                page=r["page"],
                match_line=r["match_line"],
                context_before=r["context_before"],
                context_after=r["context_after"],
                full_excerpt=r["full_excerpt"],
            )
            for r in grep_results[:15]  # Limit for response size
        ],
    )

    return QueryResponse(answer=answer, citations=citations, reasoning=reasoning)


async def _handle_standard_query(request: QueryRequest) -> QueryResponse:
    """Handle non-MCQ questions with standard hybrid search."""

    # Search for relevant chunks (hybrid search)
    try:
        results, keywords, search_info = await vector_store.search(request.question, top_k=request.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    if not results:
        return QueryResponse(
            answer="Не намерих релевантна информация в качените документи. / No relevant information found in uploaded documents.",
            citations=[],
            reasoning=Reasoning(
                keywords_extracted=keywords,
                chunks_retrieved=0,
                retrieval_summary=[],
                prompt_sent="",
                is_mcq=False,
            ),
        )

    # Generate answer with LLM
    try:
        answer, prompt_sent = await generate_answer(request.question, results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    # Format citations with match info
    citations = [
        Citation(
            filename=result["filename"],
            page=result["page"],
            excerpt=result["text"][:300] + "..." if len(result["text"]) > 300 else result["text"],
            match_type=result["match_type"],
            keyword_matches=result["keyword_matches"],
            scores=result["scores"],
        )
        for result in results
    ]

    # Build retrieval summary for reasoning
    retrieval_summary = [
        RetrievalSummary(
            source=f"{result['filename']} стр.{result['page']}",
            match_type=result["match_type"],
            keywords_found=result["keyword_matches"],
            scores=result["scores"],
        )
        for result in results
    ]

    # Build reasoning object
    reasoning = Reasoning(
        keywords_extracted=keywords,
        chunks_retrieved=len(results),
        retrieval_summary=retrieval_summary,
        prompt_sent=prompt_sent,
        is_mcq=False,
    )

    return QueryResponse(answer=answer, citations=citations, reasoning=reasoning)


@router.delete("/reset")
async def reset_database():
    """Clear all documents and vectors."""
    # Clear vector store
    try:
        vector_store.reset()
    except Exception:
        pass

    # Clear uploads directory
    for file_path in settings.upload_dir.glob("*.pdf"):
        file_path.unlink(missing_ok=True)

    return {"status": "reset complete"}
