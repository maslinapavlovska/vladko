import json
import re

import httpx

from app.config import settings


# ============================================================================
# STAGE 1: Query Analysis Prompt
# ============================================================================
ANALYZE_MCQ_PROMPT = """Given a multiple choice question, return search terms to find the answer in documents.

Question: {question}
Options: {options}

IMPORTANT: Keep all names and terms in their ORIGINAL script (Cyrillic stays Cyrillic, Latin stays Latin).
DO NOT transliterate names. Use them EXACTLY as written in the options.

Return ONLY a JSON object:
{{
  "search_terms": ["term1", "term2", ...],
  "reasoning": "Brief explanation"
}}

The search_terms MUST include:
1. Each option name EXACTLY as written (e.g., if option is "Херодот", include "Херодот" not "Herodot")
2. Key concept words from the question"""


# ============================================================================
# STAGE 3: Evidence Reasoning Prompt
# ============================================================================
REASON_MCQ_PROMPT = """You must answer a multiple choice question using ONLY the document excerpts provided below.

QUESTION:
{question}

OPTIONS:
{options}

DOCUMENT EXCERPTS (search results):
{evidence}

CRITICAL RULES:
1. You can ONLY select an answer if that exact answer option NAME appears in the excerpts above
2. If an option name (like "Херодот" or "Ратцел") is NOT found in any excerpt, you CANNOT select it
3. DO NOT use your external knowledge - ONLY what is written in the excerpts
4. If none of the option names appear in the excerpts, say "Не мога да намеря отговора в документите"

RESPOND IN THIS FORMAT:
Answer: [Letter]) [Option text] - OR - "Не мога да намеря отговора в документите"
Evidence: "[Exact quote containing the answer option name]"
Source: [filename], page [X]
Explanation: [Why this option is correct based on the excerpt]

IMPORTANT: Only select options that are EXPLICITLY mentioned in the excerpts! If you don't see the name in the excerpts, don't select it."""


# ============================================================================
# Original System Prompt (for non-MCQ questions)
# ============================================================================
SYSTEM_PROMPT = """You are a helpful multilingual assistant that answers questions based on the provided document excerpts.

CRITICAL RULES:
1. ONLY use information from the provided context. DO NOT use external knowledge.
2. Always cite sources: [Document: filename, Page: X]
3. Answer in the same language as the question.

FOR MULTIPLE CHOICE QUESTIONS (with options А, Б, В, Г, Д or A, B, C, D, E):
- Start your answer with the correct letter option (e.g., "Б) Херодот")
- Then explain WHY this is correct based on the context
- Quote the relevant text from the document that supports your answer
- If you cannot find the answer in the context, say "Не мога да намеря отговора в предоставените документи"

FOR OPEN QUESTIONS:
- Provide a direct, concise answer
- Cite the source document and page

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

Answer (remember to cite sources with document name and page number):"""

    return prompt


async def generate_answer(question: str, context_chunks: list[dict]) -> tuple[str, str]:
    """
    Generate an answer using Ollama LLM.

    Takes the question and relevant context chunks, builds a prompt,
    and returns tuple of (answer, prompt_sent).
    """
    prompt = build_prompt(question, context_chunks)

    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min for large models
        response = await client.post(
            f"{settings.ollama_host}/api/generate",
            json={
                "model": settings.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower for factual/exam questions
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["response"], prompt


async def analyze_mcq_question(question: str, options: list[str]) -> dict:
    """
    Stage 1: Ask LLM what to search for in documents.

    Returns dict with:
    - search_terms: list of terms to grep for
    - reasoning: LLM's explanation of why these terms
    """
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
                    "temperature": 0.1,  # Very low for consistent JSON output
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        raw_response = data["response"]

    # Parse JSON from response
    llm_terms = []
    reasoning = ""
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'\{[^{}]*\}', raw_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            llm_terms = result.get("search_terms", [])
            reasoning = result.get("reasoning", "")
    except json.JSONDecodeError:
        reasoning = "Failed to parse LLM response"

    # ALWAYS include original options to ensure they're searched
    # Combine LLM suggestions with original options (options take priority)
    all_terms = list(options)  # Start with original options
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
    """
    Stage 3: LLM reasons over grep results to pick the correct answer.

    Returns tuple of (answer, prompt_sent).
    """
    # Format options with letters
    options_formatted = "\n".join(
        f"{chr(ord('А') + i)}) {opt}" for i, opt in enumerate(options)
    )

    # Format evidence from grep results
    if grep_results:
        evidence_parts = []
        for i, result in enumerate(grep_results[:15], 1):  # Limit to 15 results
            evidence_parts.append(
                f"[{i}] Term: \"{result['term']}\"\n"
                f"    Source: {result['filename']}, page {result['page']}\n"
                f"    Context:\n{result['full_excerpt']}"
            )
        evidence = "\n\n".join(evidence_parts)
    else:
        evidence = "(No matches found in documents)"

    prompt = REASON_MCQ_PROMPT.format(
        question=question,
        options=options_formatted,
        evidence=evidence,
    )

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{settings.ollama_host}/api/generate",
            json={
                "model": settings.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,  # Low for factual reasoning
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["response"], prompt
