import json
import re
from difflib import SequenceMatcher
from typing import Optional

import httpx

from app.config import settings


# ============================================================================
# NEW: Deterministic MCQ Prompt - We TELL the LLM what was found
# ============================================================================
DETERMINISTIC_MCQ_PROMPT = """You are answering a multiple choice question. I have ALREADY searched the documents for you.

QUESTION:
{question}

ALL OPTIONS:
{all_options}

=== SEARCH RESULTS ===
{search_status}

{evidence_section}

=== YOUR TASK ===
{task_instruction}

RESPONSE FORMAT (you MUST follow this exactly):
Answer: [Your answer - either a letter+option OR "НЕ МОГА ДА ОПРЕДЕЛЯ" / "CANNOT DETERMINE"]
Confidence: [HIGH if option found in documents, LOW if using web search, NONE if no answer]
Evidence: "[Exact quote from the source that supports your answer]"
Source: [filename, page X] OR [Web search]
Justification: [2-3 sentences explaining WHY this is the correct answer based on the evidence]
"""

TASK_FOUND_ONE = """Based on my search, ONLY "{found_option}" was found in the documents.
You MUST select this option since it's the only one with documentary evidence.
Explain why the document text supports this as the answer."""

TASK_FOUND_MULTIPLE = """Multiple options were found in the documents: {found_options}
Review the evidence for each and select the one that BEST answers the question.
You MUST choose from these options only."""

TASK_FOUND_NONE = """NONE of the answer options were found in the uploaded documents.
{web_results}
If web results are provided, use them to answer. Otherwise respond with:
Answer: НЕ МОГА ДА ОПРЕДЕЛЯ / CANNOT DETERMINE
Confidence: NONE
Evidence: "No matching content found in documents"
Source: N/A
Justification: The answer options do not appear in the uploaded documents."""

TASK_WEB_FALLBACK = """The answer was not in the documents, but I found this from web search:
{web_summary}

Use this web information to answer the question."""


# ============================================================================
# Web Search Integration Prompt
# ============================================================================
WEB_SEARCH_PROMPT = """Search query for: {question}

I need to find which of these options is correct:
{options}

Provide factual information about which option is historically/factually correct."""


# ============================================================================
# Original System Prompt (for non-MCQ questions)
# ============================================================================
SYSTEM_PROMPT = """You are a helpful multilingual assistant that answers questions based on the provided document excerpts.

CRITICAL RULES:
1. ONLY use information from the provided context. DO NOT use external knowledge.
2. Always cite sources: [Document: filename, Page: X]
3. Answer in the same language as the question.
4. If you cannot find the answer in the context, clearly state: "Не мога да намеря отговора в предоставените документи" / "I cannot find the answer in the provided documents"

FOR OPEN QUESTIONS:
- Provide a direct, concise answer
- Cite the source document and page
- Include a brief justification for your answer

If the context doesn't contain enough information, clearly state this."""


def build_prompt(question: str, context_chunks: list[dict]) -> str:
    """Build the prompt with context and question."""
    context_parts = []

    for chunk in context_chunks:
        context_parts.append(
            f"[Source: {chunk['filename']}, Page {chunk['page']}]\n{chunk['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""{SYSTEM_PROMPT}

Context from documents:

{context}

---

Question: {question}

Answer (remember to cite sources with document name and page number, and provide justification):"""

    return prompt


def build_deterministic_mcq_prompt(
    question: str,
    options: list[str],
    found_options: dict[str, list[dict]],
    web_results: Optional[str] = None
) -> str:
    """
    Build a prompt where we TELL the LLM what was found (deterministic).
    This prevents hallucination because the LLM doesn't choose - we tell it.
    """
    # Format all options with letters
    all_options = "\n".join(
        f"{chr(ord('А') + i)}) {opt}" for i, opt in enumerate(options)
    )
    
    # Determine search status and evidence
    if len(found_options) == 0:
        search_status = "❌ NO OPTIONS FOUND in the uploaded documents."
        evidence_section = ""
        
        if web_results:
            task_instruction = TASK_WEB_FALLBACK.format(web_summary=web_results)
        else:
            task_instruction = TASK_FOUND_NONE.format(web_results="No web search results available.")
    
    elif len(found_options) == 1:
        found_option = list(found_options.keys())[0]
        search_status = f"✓ FOUND: \"{found_option}\" appears in the documents."
        
        # Build evidence section
        evidence_parts = []
        for opt, evidences in found_options.items():
            evidence_parts.append(f"\n### Evidence for \"{opt}\":")
            for ev in evidences[:3]:  # Limit to 3 evidence snippets per option
                evidence_parts.append(
                    f"  Source: {ev['filename']}, page {ev['page']}\n"
                    f"  Text: \"{ev['excerpt'][:500]}...\""
                )
        evidence_section = "\n".join(evidence_parts)
        
        task_instruction = TASK_FOUND_ONE.format(found_option=found_option)
    
    else:
        found_list = list(found_options.keys())
        search_status = f"✓ FOUND MULTIPLE: {', '.join(found_list)} appear in the documents."
        
        # Build evidence section for each found option
        evidence_parts = []
        for opt, evidences in found_options.items():
            evidence_parts.append(f"\n### Evidence for \"{opt}\":")
            for ev in evidences[:2]:
                evidence_parts.append(
                    f"  Source: {ev['filename']}, page {ev['page']}\n"
                    f"  Text: \"{ev['excerpt'][:400]}...\""
                )
        evidence_section = "\n".join(evidence_parts)
        
        task_instruction = TASK_FOUND_MULTIPLE.format(
            found_options=", ".join(f'"{opt}"' for opt in found_list)
        )
    
    return DETERMINISTIC_MCQ_PROMPT.format(
        question=question,
        all_options=all_options,
        search_status=search_status,
        evidence_section=evidence_section,
        task_instruction=task_instruction,
    )


async def generate_answer(question: str, context_chunks: list[dict]) -> tuple[str, str]:
    """Generate an answer using Ollama LLM for non-MCQ questions."""
    prompt = build_prompt(question, context_chunks)

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{settings.ollama_host}/api/generate",
            json={
                "model": settings.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["response"], prompt


async def generate_deterministic_mcq_answer(
    question: str,
    options: list[str],
    found_options: dict[str, list[dict]],
    web_results: Optional[str] = None
) -> tuple[str, str]:
    """
    Generate MCQ answer using deterministic prompt.
    The LLM is TOLD what was found, not asked to find it.
    """
    prompt = build_deterministic_mcq_prompt(
        question=question,
        options=options,
        found_options=found_options,
        web_results=web_results
    )
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{settings.ollama_host}/api/generate",
            json={
                "model": settings.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Very low for deterministic output
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["response"], prompt


async def search_web_for_answer(question: str, options: list[str]) -> Optional[dict]:
    """
    Placeholder for web search integration.
    In production, integrate with a search API (SerpAPI, Brave, etc.)
    
    Returns dict with:
    - answer: the likely correct option
    - summary: explanation from web
    - sources: list of URLs
    """
    # TODO: Implement actual web search
    # For now, return None to indicate no web results
    # 
    # Example integration with httpx:
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(
    #         "https://api.search.brave.com/res/v1/web/search",
    #         headers={"X-Subscription-Token": BRAVE_API_KEY},
    #         params={"q": f"{question} {' '.join(options)}"}
    #     )
    #     results = response.json()
    #     # Parse and return relevant info
    
    return None


def parse_llm_response(response: str) -> dict:
    """
    Parse the structured LLM response to extract components.
    Returns dict with: answer, confidence, evidence, source, justification
    """
    result = {
        "answer": None,
        "confidence": None,
        "evidence": None,
        "source": None,
        "justification": None,
        "raw_response": response,
    }
    
    # Parse each field
    patterns = {
        "answer": r"Answer:\s*(.+?)(?=\n|Confidence:|$)",
        "confidence": r"Confidence:\s*(.+?)(?=\n|Evidence:|$)",
        "evidence": r"Evidence:\s*[\"']?(.+?)[\"']?(?=\n|Source:|$)",
        "source": r"Source:\s*(.+?)(?=\n|Justification:|$)",
        "justification": r"Justification:\s*(.+?)(?=\n\n|$)",
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        if match:
            result[field] = match.group(1).strip()
    
    return result


def validate_answer_against_evidence(
    parsed_response: dict,
    found_options: dict[str, list[dict]]
) -> dict:
    """
    Post-validation: Check if the LLM's answer matches what we found.
    Adds a 'validated' field and 'validation_note' to the response.
    """
    result = parsed_response.copy()
    result["validated"] = False
    result["validation_note"] = ""
    
    answer = result.get("answer", "")
    if not answer:
        result["validation_note"] = "No answer provided"
        return result
    
    # Check if answer contains one of the found options
    answer_lower = answer.lower()
    
    for found_opt in found_options.keys():
        if found_opt.lower() in answer_lower:
            result["validated"] = True
            result["validation_note"] = f"Answer '{found_opt}' verified in documents"
            return result
    
    # Check for "cannot determine" responses
    cannot_determine_phrases = [
        "не мога да определя",
        "cannot determine", 
        "не мога да намеря",
        "cannot find",
        "n/a"
    ]
    
    for phrase in cannot_determine_phrases:
        if phrase in answer_lower:
            result["validated"] = True
            result["validation_note"] = "Correctly indicated answer not found"
            return result
    
    # If we reach here, the LLM hallucinated
    result["validation_note"] = f"WARNING: LLM selected '{answer}' but only these were found in documents: {list(found_options.keys())}"
    
    return result


# ============================================================================
# Legacy functions (kept for backwards compatibility)
# ============================================================================

ANALYZE_MCQ_PROMPT = """Given a multiple choice question, return search terms to find the answer in documents.

Question: {question}
Options: {options}

IMPORTANT: Keep all names and terms in their ORIGINAL script (Cyrillic stays Cyrillic, Latin stays Latin).

Return ONLY a JSON object:
{{
  "search_terms": ["term1", "term2", ...],
  "reasoning": "Brief explanation"
}}"""


async def analyze_mcq_question(question: str, options: list[str]) -> dict:
    """Stage 1: Ask LLM what to search for in documents."""
    prompt = ANALYZE_MCQ_PROMPT.format(
        question=question,
        options=", ".join(options)
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.ollama_host}/api/generate",
            json={
                "model": settings.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        raw_response = data["response"]

    llm_terms = []
    reasoning = ""
    try:
        json_match = re.search(r'\{[^{}]*\}', raw_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            llm_terms = result.get("search_terms", [])
            reasoning = result.get("reasoning", "")
    except json.JSONDecodeError:
        reasoning = "Failed to parse LLM response"

    all_terms = list(options)
    for term in llm_terms:
        if term not in all_terms:
            all_terms.append(term)

    return {
        "search_terms": all_terms,
        "reasoning": reasoning or "Using option names + LLM suggestions",
        "raw_response": raw_response,
    }


async def reason_over_evidence(
    question: str,
    options: list[str],
    grep_results: list[dict]
) -> tuple[str, str]:
    """Legacy function - now redirects to deterministic approach."""
    # This is kept for backwards compatibility but should use the new approach
    from app.services.vector_store import vector_store

    found_options = vector_store.validate_options_in_text(options, grep_results)
    return await generate_deterministic_mcq_answer(
        question=question,
        options=options,
        found_options=found_options,
        web_results=None
    )


# ============================================================================
# Citation Verification for Open Questions
# ============================================================================

def extract_quotes(text: str) -> list[str]:
    """
    Extract quoted text from LLM response.
    Handles various quote styles: "...", «...», '...', and Evidence: fields.
    """
    quotes = []

    # Pattern for double quotes (ASCII and Unicode variants)
    double_quote_patterns = [
        r'"([^"]{10,})"',           # ASCII double quotes
        r'"([^"]{10,})"',           # Unicode curly quotes
        r'„([^"]{10,})"',           # German/Bulgarian style quotes
        r'«([^»]{10,})»',           # Guillemets (French/Bulgarian)
    ]

    for pattern in double_quote_patterns:
        matches = re.findall(pattern, text)
        quotes.extend(matches)

    # Also extract text after "Evidence:" marker if present
    evidence_match = re.search(
        r'Evidence:\s*["\']?(.+?)["\']?(?=\n|Source:|$)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if evidence_match:
        evidence_text = evidence_match.group(1).strip()
        # Only add if it's substantial and not already captured
        if len(evidence_text) >= 10 and evidence_text not in quotes:
            quotes.append(evidence_text)

    # Deduplicate while preserving order
    seen = set()
    unique_quotes = []
    for q in quotes:
        q_clean = q.strip()
        if q_clean not in seen and len(q_clean) >= 10:
            seen.add(q_clean)
            unique_quotes.append(q_clean)

    return unique_quotes


def verify_quote_in_text(quote: str, source_text: str, threshold: float = 0.7) -> dict:
    """
    Check if a quote exists in the source text using fuzzy matching.

    Returns dict with:
    - verified: bool
    - match_ratio: float (0-1)
    - best_match: str (the closest matching substring found)
    """
    quote_lower = quote.lower().strip()
    source_lower = source_text.lower()

    # First try exact substring match
    if quote_lower in source_lower:
        return {
            "verified": True,
            "match_ratio": 1.0,
            "best_match": quote,
            "match_type": "exact"
        }

    # Try fuzzy matching with sliding window
    quote_len = len(quote_lower)
    best_ratio = 0.0
    best_match = ""

    # Slide a window of similar size through the source
    window_sizes = [quote_len, int(quote_len * 0.8), int(quote_len * 1.2)]

    for window_size in window_sizes:
        if window_size > len(source_lower):
            continue

        for i in range(0, len(source_lower) - window_size + 1, max(1, window_size // 4)):
            window = source_lower[i:i + window_size]
            ratio = SequenceMatcher(None, quote_lower, window).ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_match = source_text[i:i + window_size]

    return {
        "verified": best_ratio >= threshold,
        "match_ratio": round(best_ratio, 3),
        "best_match": best_match if best_ratio >= threshold else "",
        "match_type": "fuzzy" if best_ratio >= threshold else "none"
    }


def verify_quotes_in_context(
    quotes: list[str],
    context_chunks: list[dict],
    threshold: float = 0.7
) -> list[dict]:
    """
    Verify all extracted quotes against the retrieved context chunks.

    Returns list of verification results, one per quote.
    """
    results = []

    # Combine all chunk text for searching
    all_text = "\n".join(chunk.get("text", "") for chunk in context_chunks)

    for quote in quotes:
        # Try to verify against combined text first
        verification = verify_quote_in_text(quote, all_text, threshold)

        # If verified, try to find which specific chunk it came from
        source_chunk = None
        if verification["verified"]:
            for chunk in context_chunks:
                chunk_text = chunk.get("text", "")
                if verify_quote_in_text(quote, chunk_text, threshold)["verified"]:
                    source_chunk = {
                        "filename": chunk.get("filename", "Unknown"),
                        "page": chunk.get("page", 0)
                    }
                    break

        results.append({
            "quote": quote[:100] + "..." if len(quote) > 100 else quote,
            "verified": verification["verified"],
            "match_ratio": verification["match_ratio"],
            "match_type": verification["match_type"],
            "source": source_chunk
        })

    return results
