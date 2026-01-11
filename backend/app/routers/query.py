from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from app.config import settings
from app.services.vector_store import vector_store
from app.services.llm_service import (
    generate_answer,
    generate_deterministic_mcq_answer,
    analyze_mcq_question,
    search_web_for_answer,
    parse_llm_response,
    validate_answer_against_evidence,
    extract_quotes,
    verify_quotes_in_context,
)

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    enable_web_fallback: bool = True  # NEW: Allow web search if not found


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
    search_terms: list[str]
    reasoning: str
    raw_response: Optional[str] = None


class GrepResult(BaseModel):
    term: str
    filename: str
    page: int
    match_line: str
    context_before: list[str]
    context_after: list[str]
    full_excerpt: str


class OptionValidation(BaseModel):
    """NEW: Shows which options were found in documents."""
    option: str
    found_in_documents: bool
    evidence_count: int
    sources: list[str]


class AnswerJustification(BaseModel):
    """NEW: Structured justification for the answer."""
    answer: Optional[str]
    confidence: str  # HIGH, LOW, NONE
    evidence_quote: Optional[str]
    source: Optional[str]
    explanation: str
    validated: bool
    validation_note: str


class QuoteVerification(BaseModel):
    """Verification result for a quoted citation in open questions."""
    quote: str
    verified: bool
    match_ratio: float
    match_type: str  # exact, fuzzy, none
    source: Optional[dict] = None


class CitationVerificationResult(BaseModel):
    """Overall citation verification summary for open questions."""
    quotes_found: int
    quotes_verified: int
    all_verified: bool
    verifications: list[QuoteVerification]


class Reasoning(BaseModel):
    # Original fields
    keywords_extracted: list[str] = []
    chunks_retrieved: int = 0
    retrieval_summary: list[RetrievalSummary] = []
    prompt_sent: str = ""
    is_mcq: bool = False
    mcq_options: list[str] = []
    # Two-stage MCQ fields
    stage1_analysis: Optional[Stage1Analysis] = None
    stage2_grep_results: Optional[list[GrepResult]] = None
    # Validation and justification fields
    options_validation: Optional[list[OptionValidation]] = None
    justification: Optional[AnswerJustification] = None
    used_web_search: bool = False
    web_search_query: Optional[str] = None
    # Citation verification for open questions
    citation_verification: Optional[CitationVerificationResult] = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    reasoning: Reasoning


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents with hybrid search, deterministic MCQ handling, and justification."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Detect if this is an MCQ question
    is_mcq, mcq_options = vector_store._detect_mcq_options(request.question)

    if is_mcq and mcq_options:
        return await _handle_mcq_query_deterministic(
            request.question, 
            mcq_options,
            enable_web_fallback=request.enable_web_fallback
        )
    else:
        return await _handle_standard_query(request)


async def _handle_mcq_query_deterministic(
    question: str, 
    mcq_options: list[str],
    enable_web_fallback: bool = True
) -> QueryResponse:
    """
    NEW: Deterministic MCQ handling that prevents hallucination.
    
    Pipeline:
    1. Search documents for ALL options (grep search)
    2. Validate which options actually appear in text (deterministic)
    3. If exactly 1 found → that's the answer
    4. If 0 found → web search fallback (optional)
    5. If multiple found → ask LLM to choose from ONLY found options
    6. Validate LLM response matches what we found
    7. Return with full justification
    """
    
    # Stage 1: Get search terms (options + related terms)
    try:
        analysis = await analyze_mcq_question(question, mcq_options)
        search_terms = analysis.get("search_terms", mcq_options)
    except Exception as e:
        analysis = {
            "search_terms": mcq_options,
            "reasoning": f"Fallback due to error: {str(e)}",
        }
        search_terms = mcq_options

    # Stage 2: Grep search with context
    grep_results = vector_store.grep_search(search_terms, context_lines=3)
    
    # Stage 3: CRITICAL - Deterministically validate which options appear in documents
    # Also search in ALL documents, not just grep results
    found_options = {}
    for option in mcq_options:
        # Check in grep results
        option_lower = option.lower().strip()
        option_evidence = []
        
        for result in grep_results:
            excerpt_lower = result.get("full_excerpt", "").lower()
            if option_lower in excerpt_lower:
                option_evidence.append({
                    "filename": result["filename"],
                    "page": result["page"],
                    "excerpt": result["full_excerpt"],
                    "match_line": result["match_line"],
                })
        
        # Also do a comprehensive search across ALL documents
        all_doc_matches = vector_store.find_option_in_all_documents(option)
        for match in all_doc_matches:
            # Avoid duplicates
            is_duplicate = any(
                ev["filename"] == match["filename"] and ev["page"] == match["page"]
                for ev in option_evidence
            )
            if not is_duplicate:
                option_evidence.append({
                    "filename": match["filename"],
                    "page": match["page"],
                    "excerpt": match["context"],
                    "match_line": match["match_line"],
                })
        
        if option_evidence:
            found_options[option] = option_evidence

    # Build options validation for transparency
    options_validation = [
        OptionValidation(
            option=opt,
            found_in_documents=opt in found_options,
            evidence_count=len(found_options.get(opt, [])),
            sources=[
                f"{ev['filename']} p.{ev['page']}" 
                for ev in found_options.get(opt, [])[:3]
            ]
        )
        for opt in mcq_options
    ]

    # Stage 4: Determine answer based on what we found
    web_results = None
    used_web_search = False
    
    if len(found_options) == 0 and enable_web_fallback:
        # No options found - try web search
        web_results_data = await search_web_for_answer(question, mcq_options)
        if web_results_data:
            web_results = web_results_data.get("summary", "")
            used_web_search = True
    
    # Stage 5: Generate answer using deterministic prompt
    try:
        answer, prompt_sent = await generate_deterministic_mcq_answer(
            question=question,
            options=mcq_options,
            found_options=found_options,
            web_results=web_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    # Stage 6: Parse and validate LLM response
    parsed = parse_llm_response(answer)
    validated = validate_answer_against_evidence(parsed, found_options)
    
    # Build justification
    justification = AnswerJustification(
        answer=validated.get("answer"),
        confidence=validated.get("confidence", "UNKNOWN"),
        evidence_quote=validated.get("evidence"),
        source=validated.get("source"),
        explanation=validated.get("justification", ""),
        validated=validated.get("validated", False),
        validation_note=validated.get("validation_note", ""),
    )

    # If validation failed (LLM hallucinated), override with correct answer
    if not validated.get("validated", False) and len(found_options) == 1:
        correct_option = list(found_options.keys())[0]
        evidence = found_options[correct_option][0]
        
        # Override the hallucinated answer
        answer = f"""Answer: {correct_option}
Confidence: HIGH (deterministically verified)
Evidence: "{evidence['match_line']}"
Source: {evidence['filename']}, page {evidence['page']}
Justification: This option was the ONLY one found in the uploaded documents. The system verified this deterministically.

⚠️ Note: The LLM initially selected a different answer, but validation showed only "{correct_option}" appears in your documents."""
        
        justification.answer = correct_option
        justification.confidence = "HIGH"
        justification.evidence_quote = evidence["match_line"]
        justification.source = f"{evidence['filename']}, page {evidence['page']}"
        justification.validated = True
        justification.validation_note = f"Auto-corrected from LLM hallucination to verified answer: {correct_option}"

    # Format citations from found options
    citations = []
    for opt, evidences in found_options.items():
        for ev in evidences[:2]:  # Limit citations per option
            citations.append(
                Citation(
                    filename=ev["filename"],
                    page=ev["page"],
                    excerpt=ev["excerpt"][:300] + "..." if len(ev["excerpt"]) > 300 else ev["excerpt"],
                    match_type="verified",
                    keyword_matches=[opt],
                    scores={"verified_match": 1.0},
                )
            )

    # Build reasoning with full transparency
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
            for r in grep_results[:15]
        ],
        options_validation=options_validation,
        justification=justification,
        used_web_search=used_web_search,
    )

    return QueryResponse(answer=answer, citations=citations, reasoning=reasoning)


async def _handle_standard_query(request: QueryRequest) -> QueryResponse:
    """Handle non-MCQ questions with standard hybrid search."""

    try:
        results, keywords, search_info = await vector_store.search(
            request.question, top_k=request.top_k
        )
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

    try:
        answer, prompt_sent = await generate_answer(request.question, results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    # Citation verification: extract quotes and verify against source chunks
    quotes = extract_quotes(answer)
    citation_verification = None

    if quotes:
        verifications = verify_quotes_in_context(quotes, results)
        verified_count = sum(1 for v in verifications if v["verified"])

        citation_verification = CitationVerificationResult(
            quotes_found=len(quotes),
            quotes_verified=verified_count,
            all_verified=(verified_count == len(quotes)),
            verifications=[
                QuoteVerification(
                    quote=v["quote"],
                    verified=v["verified"],
                    match_ratio=v["match_ratio"],
                    match_type=v["match_type"],
                    source=v["source"]
                )
                for v in verifications
            ]
        )

        # Add warning if any quotes couldn't be verified
        unverified = [v for v in verifications if not v["verified"]]
        if unverified:
            warning = "\n\n⚠️ Внимание / Warning: "
            if len(unverified) == len(quotes):
                warning += "Цитираният текст не беше намерен в документите. / The cited text could not be verified in the documents."
            else:
                warning += f"{len(unverified)} от {len(quotes)} цитата не бяха потвърдени. / {len(unverified)} of {len(quotes)} citations could not be verified."
            answer += warning

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

    retrieval_summary = [
        RetrievalSummary(
            source=f"{result['filename']} стр.{result['page']}",
            match_type=result["match_type"],
            keywords_found=result["keyword_matches"],
            scores=result["scores"],
        )
        for result in results
    ]

    reasoning = Reasoning(
        keywords_extracted=keywords,
        chunks_retrieved=len(results),
        retrieval_summary=retrieval_summary,
        prompt_sent=prompt_sent,
        is_mcq=False,
        citation_verification=citation_verification,
    )

    return QueryResponse(answer=answer, citations=citations, reasoning=reasoning)


@router.delete("/reset")
async def reset_database():
    """Clear all documents and vectors."""
    try:
        vector_store.reset()
    except Exception:
        pass

    for file_path in settings.upload_dir.glob("*.pdf"):
        file_path.unlink(missing_ok=True)

    return {"status": "reset complete"}
