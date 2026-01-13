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
        # Legacy collection for backwards compatibility
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )
        # Cache for project collections
        self._project_collections: dict[str, Any] = {}

    def get_project_collection(self, project_id: str) -> Any:
        """Get or create a ChromaDB collection for a project."""
        if project_id not in self._project_collections:
            collection_name = f"project_{project_id}"
            self._project_collections[project_id] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._project_collections[project_id]

    def delete_project_collection(self, project_id: str) -> None:
        """Delete a project's ChromaDB collection."""
        collection_name = f"project_{project_id}"
        try:
            self.client.delete_collection(collection_name)
            self._project_collections.pop(project_id, None)
        except ValueError:
            pass  # Collection doesn't exist

    def _get_collection(self, project_id: str = None) -> Any:
        """Get collection - project-specific if project_id provided, else legacy."""
        if project_id:
            return self.get_project_collection(project_id)
        return self.collection

    async def add_chunks(self, filename: str, chunks: list[dict], project_id: str = None, document_id: str = None) -> None:
        """Add document chunks to the vector store."""
        if not chunks:
            return

        collection = self._get_collection(project_id)

        texts = [chunk["text"] for chunk in chunks]
        embeddings = await get_embeddings_batch(texts)

        # Include document_id in the ID if provided (for project-based storage)
        if document_id:
            ids = [f"{document_id}_p{chunk['page']}_c{chunk['chunk_id']}" for chunk in chunks]
            metadatas = [{"filename": filename, "page": chunk["page"], "document_id": document_id} for chunk in chunks]
        else:
            ids = [f"{filename}_p{chunk['page']}_c{chunk['chunk_id']}" for chunk in chunks]
            metadatas = [{"filename": filename, "page": chunk["page"]} for chunk in chunks]

        documents = texts

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def _detect_mcq_options(self, query: str) -> tuple[bool, list[str]]:
        """Detect if query is MCQ format and extract answer options."""
        options = MCQ_PATTERN.findall(query)
        if len(options) >= 2:
            cleaned = [opt.strip() for opt in options if opt.strip()]
            return True, cleaned
        return False, []

    def _extract_keywords(self, query: str, mcq_options: list[str] = None) -> list[str]:
        """Extract meaningful keywords from query."""
        words = re.findall(r'[\w\u0400-\u04FF]+', query.lower())
        keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]

        if mcq_options:
            for option in mcq_options:
                option_words = re.findall(r'[\w\u0400-\u04FF]+', option.lower())
                for word in option_words:
                    if word not in keywords and len(word) > 2:
                        keywords.append(word)

        return keywords

    def _keyword_search(self, all_data: dict, keywords: list[str]) -> dict[str, dict]:
        """Search for exact keyword matches in chunks."""
        results = {}

        if not keywords or not all_data.get("documents"):
            return results

        for i, doc in enumerate(all_data["documents"]):
            chunk_id = all_data["ids"][i]
            doc_lower = doc.lower()

            matches = [kw for kw in keywords if kw in doc_lower]

            if matches:
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
        """Merge keyword and semantic results with combined scoring."""
        merged = {}

        if semantic_results.get("documents") and semantic_results["documents"][0]:
            for i, doc in enumerate(semantic_results["documents"][0]):
                chunk_id = semantic_results["ids"][0][i]
                distance = semantic_results["distances"][0][i]
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

        for chunk_id, kw_data in keyword_results.items():
            if chunk_id in merged:
                merged[chunk_id]["keyword_score"] = kw_data["keyword_score"]
                merged[chunk_id]["keyword_matches"] = kw_data["keyword_matches"]
                merged[chunk_id]["match_type"] = "both"
            else:
                merged[chunk_id] = {
                    **kw_data,
                    "semantic_score": 0,
                    "match_type": "keyword",
                }

        KEYWORD_WEIGHT = 0.7
        SEMANTIC_WEIGHT = 0.3
        BOTH_BONUS = 0.2

        for chunk_id, data in merged.items():
            both_bonus = BOTH_BONUS if data["match_type"] == "both" else 0
            data["combined_score"] = (
                data["keyword_score"] * KEYWORD_WEIGHT +
                data["semantic_score"] * SEMANTIC_WEIGHT +
                both_bonus
            )

        sorted_results = sorted(
            merged.values(),
            key=lambda x: x["combined_score"],
            reverse=True,
        )[:top_k]

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

    async def search(self, query: str, top_k: int = 5, project_id: str = None) -> tuple[list[dict], list[str], dict]:
        """Hybrid search: combine keyword and semantic search."""
        collection = self._get_collection(project_id)

        if collection.count() == 0:
            return [], [], {"is_mcq": False, "mcq_options": []}

        is_mcq, mcq_options = self._detect_mcq_options(query)
        effective_top_k = top_k * 2 if is_mcq else top_k

        keywords = self._extract_keywords(query, mcq_options if is_mcq else None)
        all_data = collection.get(include=["documents", "metadatas"])
        keyword_results = self._keyword_search(all_data, keywords)

        query_embedding = await get_embedding(query)
        semantic_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(effective_top_k * 2, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        merged = self._merge_results(keyword_results, semantic_results, keywords, effective_top_k)

        search_info = {
            "is_mcq": is_mcq,
            "mcq_options": mcq_options,
        }

        return merged, keywords, search_info

    def grep_search(
        self,
        search_terms: list[str],
        context_lines: int = 3,
        project_id: str = None
    ) -> list[dict]:
        """Grep-style search: find exact matches with surrounding context."""
        results = []
        collection = self._get_collection(project_id)
        all_data = collection.get(include=["documents", "metadatas"])

        if not all_data.get("documents"):
            return results

        for i, doc in enumerate(all_data["documents"]):
            lines = doc.split('\n')
            doc_lower = doc.lower()
            metadata = all_data["metadatas"][i]

            for term in search_terms:
                term_lower = term.lower()

                if term_lower not in doc_lower:
                    continue

                for line_num, line in enumerate(lines):
                    if term_lower in line.lower():
                        start = max(0, line_num - context_lines)
                        end = min(len(lines), line_num + 1 + context_lines)

                        before = lines[start:line_num]
                        after = lines[line_num + 1:end]

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

    def validate_options_in_text(
        self,
        options: list[str],
        grep_results: list[dict]
    ) -> dict[str, list[dict]]:
        """
        CRITICAL: Deterministically check which MCQ options appear in the retrieved text.
        
        Returns a dict mapping each option to the evidence where it was found.
        This is the KEY fix for hallucination - we don't ask the LLM to find options,
        we TELL it which options were found.
        """
        found_options = {}
        
        # Combine all retrieved text
        all_text = ""
        for result in grep_results:
            all_text += " " + result.get("full_excerpt", "") + " " + result.get("match_line", "")
        
        all_text_lower = all_text.lower()
        
        for option in options:
            option_lower = option.lower().strip()
            
            # Check if option appears in any retrieved text
            if option_lower in all_text_lower:
                # Find all evidence snippets containing this option
                evidence = []
                for result in grep_results:
                    excerpt_lower = result.get("full_excerpt", "").lower()
                    match_line_lower = result.get("match_line", "").lower()
                    
                    if option_lower in excerpt_lower or option_lower in match_line_lower:
                        evidence.append({
                            "filename": result["filename"],
                            "page": result["page"],
                            "excerpt": result["full_excerpt"],
                            "match_line": result["match_line"],
                        })
                
                if evidence:
                    found_options[option] = evidence
        
        return found_options

    def get_all_text_for_search(self, project_id: str = None) -> str:
        """Get all document text for comprehensive option search."""
        collection = self._get_collection(project_id)
        all_data = collection.get(include=["documents"])
        if not all_data.get("documents"):
            return ""
        return " ".join(all_data["documents"])

    def find_option_in_all_documents(self, option: str, project_id: str = None) -> list[dict]:
        """
        Search for a specific option across ALL documents (not just grep results).
        Returns list of matches with page/file info.
        """
        results = []
        collection = self._get_collection(project_id)
        all_data = collection.get(include=["documents", "metadatas"])
        
        if not all_data.get("documents"):
            return results
        
        option_lower = option.lower().strip()
        
        for i, doc in enumerate(all_data["documents"]):
            if option_lower in doc.lower():
                # Find the specific line containing the option
                lines = doc.split('\n')
                for line_num, line in enumerate(lines):
                    if option_lower in line.lower():
                        # Get context
                        start = max(0, line_num - 2)
                        end = min(len(lines), line_num + 3)
                        context = "\n".join(lines[start:end])
                        
                        results.append({
                            "filename": all_data["metadatas"][i]["filename"],
                            "page": all_data["metadatas"][i]["page"],
                            "match_line": line.strip(),
                            "context": context,
                        })
        
        return results

    def delete_document(self, filename: str, project_id: str = None) -> None:
        """Delete all chunks for a document."""
        collection = self._get_collection(project_id)
        results = collection.get(
            where={"filename": filename},
            include=[],
        )

        if results["ids"]:
            collection.delete(ids=results["ids"])

    def reset(self) -> None:
        """Delete and recreate the collection."""
        self.client.delete_collection("documents")
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )


# Global instance
vector_store = VectorStore()
