import re
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Any

from app.config import settings
from app.services.embedding_service import get_embedding, get_embeddings_batch

# Stopwords for keyword extraction (Bulgarian + English)
STOPWORDS = {
    # English
    'what', 'which', 'who', 'where', 'when', 'why', 'how',
    'is', 'are', 'was', 'were', 'the', 'a', 'an', 'and',
    'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'from', 'as', 'into', 'about',
    # Bulgarian common words
    'какво', 'кой', 'коя', 'кое', 'кои', 'къде', 'кога',
    'защо', 'как', 'е', 'са', 'и', 'или', 'но', 'в',
    'на', 'за', 'от', 'с', 'по', 'има', 'имат', 'ли',
    'се', 'не', 'да', 'че', 'като', 'това', 'тези',
    'при', 'след', 'между', 'под', 'над', 'без'
}

# MCQ option patterns (Bulgarian and English)
# Matches А) Option text Б) ... or A) Option text B) ...
MCQ_PATTERN = re.compile(
    r'[АБВГДABCDE]\s*\)\s*(.+?)(?=\s+[АБВГДABCDE]\s*\)|$)',
    re.IGNORECASE
)


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    async def add_chunks(self, filename: str, chunks: list[dict]) -> None:
        """
        Add document chunks to the vector store.

        Each chunk should have: text, page, chunk_id
        """
        if not chunks:
            return

        # Generate embeddings for all chunks
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await get_embeddings_batch(texts)

        # Prepare data for ChromaDB
        ids = [f"{filename}_p{chunk['page']}_c{chunk['chunk_id']}" for chunk in chunks]
        documents = texts
        metadatas = [{"filename": filename, "page": chunk["page"]} for chunk in chunks]

        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def _detect_mcq_options(self, query: str) -> tuple[bool, list[str]]:
        """
        Detect if query is MCQ format and extract answer options.
        Returns (is_mcq, list of option texts).
        """
        # Look for patterns like "А) Херодот" or "A) Herodot"
        options = MCQ_PATTERN.findall(query)

        if len(options) >= 2:  # At least 2 options to be considered MCQ
            # Clean up options - strip whitespace
            cleaned = [opt.strip() for opt in options if opt.strip()]
            return True, cleaned

        return False, []

    def _extract_keywords(self, query: str, mcq_options: list[str] = None) -> list[str]:
        """
        Extract meaningful keywords from query.
        Handles Bulgarian and English text.
        If mcq_options provided, adds those as high-priority keywords.
        """
        # Regex to match words including Cyrillic characters
        words = re.findall(r'[\w\u0400-\u04FF]+', query.lower())

        # Filter: remove stopwords and very short words
        keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]

        # For MCQ: add each option as a keyword (these are high-value search terms)
        if mcq_options:
            for option in mcq_options:
                # Extract words from each option
                option_words = re.findall(r'[\w\u0400-\u04FF]+', option.lower())
                for word in option_words:
                    if word not in keywords and len(word) > 2:
                        keywords.append(word)

        return keywords

    def _keyword_search(self, all_data: dict, keywords: list[str]) -> dict[str, dict]:
        """
        Search for exact keyword matches in chunks.

        Returns dict mapping chunk_id to match info.
        """
        results = {}

        if not keywords or not all_data.get("documents"):
            return results

        for i, doc in enumerate(all_data["documents"]):
            chunk_id = all_data["ids"][i]
            doc_lower = doc.lower()

            # Find which keywords appear in this chunk
            matches = [kw for kw in keywords if kw in doc_lower]

            if matches:
                # Score = percentage of keywords that matched
                score = len(matches) / len(keywords)
                results[chunk_id] = {
                    "text": doc,
                    "filename": all_data["metadatas"][i]["filename"],
                    "page": all_data["metadatas"][i]["page"],
                    "chunk_id": chunk_id,
                    "keyword_score": score,
                    "keyword_matches": matches,
                }

        return results

    def _merge_results(
        self,
        keyword_results: dict[str, dict],
        semantic_results: dict,
        keywords: list[str],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """
        Merge keyword and semantic results with combined scoring.
        Prioritizes chunks that match both methods.
        """
        merged = {}

        # Step 1: Add all semantic results
        if semantic_results.get("documents") and semantic_results["documents"][0]:
            for i, doc in enumerate(semantic_results["documents"][0]):
                chunk_id = semantic_results["ids"][0][i]
                distance = semantic_results["distances"][0][i]

                # Convert cosine distance to similarity (0=identical, 2=opposite)
                semantic_score = max(0, 1 - distance)

                merged[chunk_id] = {
                    "text": doc,
                    "filename": semantic_results["metadatas"][0][i]["filename"],
                    "page": semantic_results["metadatas"][0][i]["page"],
                    "chunk_id": chunk_id,
                    "semantic_score": semantic_score,
                    "keyword_score": 0,
                    "keyword_matches": [],
                    "match_type": "semantic",
                }

        # Step 2: Merge in keyword results
        for chunk_id, kw_data in keyword_results.items():
            if chunk_id in merged:
                # This chunk matched BOTH methods - very high signal
                merged[chunk_id]["keyword_score"] = kw_data["keyword_score"]
                merged[chunk_id]["keyword_matches"] = kw_data["keyword_matches"]
                merged[chunk_id]["match_type"] = "both"
            else:
                # Keyword-only match (semantic search missed it)
                merged[chunk_id] = {
                    **kw_data,
                    "semantic_score": 0,
                    "match_type": "keyword",
                }

        # Step 3: Calculate combined score
        KEYWORD_WEIGHT = 0.7   # Keywords are strong signal for factual queries
        SEMANTIC_WEIGHT = 0.3  # Semantic helps with paraphrasing
        BOTH_BONUS = 0.2       # Reward chunks matching both methods

        for chunk_id, data in merged.items():
            both_bonus = BOTH_BONUS if data["match_type"] == "both" else 0
            data["combined_score"] = (
                data["keyword_score"] * KEYWORD_WEIGHT +
                data["semantic_score"] * SEMANTIC_WEIGHT +
                both_bonus
            )

        # Step 4: Sort and return top-k
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x["combined_score"],
            reverse=True,
        )[:top_k]

        # Format output
        return [
            {
                "text": r["text"],
                "filename": r["filename"],
                "page": r["page"],
                "chunk_id": r["chunk_id"],
                "match_type": r["match_type"],
                "keyword_matches": r["keyword_matches"],
                "scores": {
                    "combined": round(r["combined_score"], 3),
                    "keyword": round(r["keyword_score"], 3),
                    "semantic": round(r["semantic_score"], 3),
                },
            }
            for r in sorted_results
        ]

    async def search(self, query: str, top_k: int = 5) -> tuple[list[dict], list[str], dict]:
        """
        Hybrid search: combine keyword and semantic search.

        Returns tuple of (results, keywords_extracted, search_info).
        Each result has: text, filename, page, match_type, keyword_matches, scores
        search_info contains: is_mcq, mcq_options
        """
        # Check if collection is empty
        if self.collection.count() == 0:
            return [], [], {"is_mcq": False, "mcq_options": []}

        # Step 1: Detect if this is a multiple choice question
        is_mcq, mcq_options = self._detect_mcq_options(query)

        # For MCQ, increase top_k to get more context
        effective_top_k = top_k * 2 if is_mcq else top_k

        # Step 2: Extract keywords (including MCQ options if present)
        keywords = self._extract_keywords(query, mcq_options if is_mcq else None)

        # Step 3: Get all chunks for keyword search
        all_data = self.collection.get(include=["documents", "metadatas"])

        # Step 4: Keyword search (grep-style)
        keyword_results = self._keyword_search(all_data, keywords)

        # Step 5: Semantic search
        query_embedding = await get_embedding(query)
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(effective_top_k * 2, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        # Step 6: Merge and rank
        merged = self._merge_results(keyword_results, semantic_results, keywords, effective_top_k)

        search_info = {
            "is_mcq": is_mcq,
            "mcq_options": mcq_options,
        }

        return merged, keywords, search_info

    def grep_search(
        self,
        search_terms: list[str],
        context_lines: int = 3
    ) -> list[dict]:
        """
        Grep-style search: find exact matches with surrounding context.

        For each search term, finds all occurrences in stored documents
        and returns the matching line plus N lines before/after.

        Returns list of:
        {
            "term": "херодот",
            "filename": "geo.pdf",
            "page": 15,
            "match_line": "Херодот е смятан за баща...",
            "context_before": ["line1", "line2"],
            "context_after": ["line3", "line4"],
            "full_excerpt": "...before...>>> MATCH ...after..."
        }
        """
        results = []

        # Get all documents from the collection
        all_data = self.collection.get(include=["documents", "metadatas"])

        if not all_data.get("documents"):
            return results

        for i, doc in enumerate(all_data["documents"]):
            lines = doc.split('\n')
            doc_lower = doc.lower()
            metadata = all_data["metadatas"][i]

            for term in search_terms:
                term_lower = term.lower()

                # Check if term exists in this document at all
                if term_lower not in doc_lower:
                    continue

                # Find which line(s) contain the match
                for line_num, line in enumerate(lines):
                    if term_lower in line.lower():
                        # Extract context lines before and after
                        start = max(0, line_num - context_lines)
                        end = min(len(lines), line_num + 1 + context_lines)

                        before = lines[start:line_num]
                        after = lines[line_num + 1:end]

                        # Build full excerpt with highlighted match line
                        excerpt_lines = (
                            before +
                            [f">>> {line.strip()}"] +
                            after
                        )

                        results.append({
                            "term": term,
                            "filename": metadata["filename"],
                            "page": metadata["page"],
                            "match_line": line.strip(),
                            "context_before": [l.strip() for l in before],
                            "context_after": [l.strip() for l in after],
                            "full_excerpt": "\n".join(l.strip() for l in excerpt_lines if l.strip()),
                        })

        return results

    def delete_document(self, filename: str) -> None:
        """Delete all chunks for a document."""
        # Get all IDs for this document
        results = self.collection.get(
            where={"filename": filename},
            include=[],
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    def reset(self) -> None:
        """Delete and recreate the collection."""
        self.client.delete_collection("documents")
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )


# Global instance
vector_store = VectorStore()
