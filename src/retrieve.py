"""Query embedding, vector search, and hybrid reranking."""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from src.embeddings import Embedder, content_tokens
from src.vector_store import SearchHit, VectorStore

LOGGER = logging.getLogger(__name__)


class EmptyKnowledgeBaseError(RuntimeError):
    """Raised when a query is made before the vector store is populated."""


@dataclass(slots=True)
class RetrievedChunk:
    """A reranked search result ready to be cited in a generated answer."""

    id: str
    text: str
    source: str
    title: str
    heading: str
    chunk_index: int
    score: float
    vector_score: float
    lexical_score: float
    metadata: dict[str, Any]

    @classmethod
    def from_hit(
        cls,
        hit: SearchHit,
        *,
        score: float,
        vector_score: float,
        lexical_score: float,
    ) -> "RetrievedChunk":
        return cls(
            id=hit.id,
            text=hit.text,
            source=hit.source,
            title=hit.title,
            heading=hit.heading,
            chunk_index=hit.chunk_index,
            score=round(score, 6),
            vector_score=round(vector_score, 6),
            lexical_score=round(lexical_score, 6),
            metadata=hit.metadata,
        )


def _normalize_question(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def lexical_score(question: str, document: str) -> float:
    """A small, explainable lexical score used to complement vector similarity.

    It combines query-term coverage with saturated term frequency. This is not a
    replacement for BM25 at scale; it is enough to keep exact policy names and
    identifiers (P1, SSO, 30 days) from being lost in embedding noise.
    """
    query_terms = set(content_tokens(question))
    if not query_terms:
        return 0.0
    document_terms = content_tokens(document)
    if not document_terms:
        return 0.0

    counts = Counter(document_terms)
    coverage = sum(1 for term in query_terms if term in counts) / len(query_terms)
    saturated_tf = sum(min(counts[term], 3) / 3 for term in query_terms) / len(query_terms)
    score = 0.65 * coverage + 0.35 * saturated_tf

    normalized_question = _normalize_question(question)
    normalized_document = _normalize_question(document)
    if len(normalized_question) >= 12 and normalized_question in normalized_document:
        score = min(1.0, score + 0.15)
    return score


class Retriever:
    """Embed queries, fetch candidates from the store, and rerank them."""

    def __init__(self, settings, store: VectorStore, embedder: Embedder) -> None:
        self.settings = settings
        self.store = store
        self.embedder = embedder

    def retrieve(self, question: str, *, top_k: int | None = None) -> list[RetrievedChunk]:
        question = question.strip()
        if len(question) < 2:
            raise ValueError("Question must contain at least two characters")

        total = self.store.count()
        if total == 0:
            raise EmptyKnowledgeBaseError(
                "The vector store is empty. Run `python -m src.ingest` before querying."
            )

        requested_k = top_k if top_k is not None else self.settings.top_k
        requested_k = max(1, min(int(requested_k), 20))
        candidate_count = max(self.settings.retrieval_candidates, requested_k * 3)
        candidate_count = min(candidate_count, total)

        query_embedding = self.embedder.embed_query(question)
        hits = self.store.search(query_embedding, candidate_count)
        if not hits:
            return []

        # Do NOT min-max normalize cosine scores: when every candidate is a weak
        # match, min-max turns noise into a perfect 1.0 and can outrank a clearly
        # relevant chunk. Absolute cosine (clamped at zero) is monotonic and stable.
        # The hashing fallback is lexical by nature, so give its exact-term signal
        # more weight than a neural model needs.
        if self.embedder.name == "hash":
            semantic_weight, lexical_weight = 0.40, 0.60
        else:
            semantic_weight, lexical_weight = 0.70, 0.30

        reranked: list[RetrievedChunk] = []
        for hit in hits:
            semantic = max(0.0, hit.score)
            lexical = lexical_score(question, hit.text)
            final = semantic_weight * semantic + lexical_weight * lexical
            reranked.append(
                RetrievedChunk.from_hit(
                    hit,
                    score=final,
                    vector_score=hit.score,
                    lexical_score=lexical,
                )
            )

        reranked.sort(key=lambda chunk: chunk.score, reverse=True)
        reranked = [chunk for chunk in reranked if chunk.score >= self.settings.min_retrieval_score]
        result = reranked[:requested_k]

        LOGGER.info(
            "Retrieved %d chunks for %r (candidates=%d, top_score=%.3f)",
            len(result),
            question[:80],
            len(hits),
            result[0].score if result else 0.0,
        )
        return result


def format_sources(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    """Serialize retrieval results for the API response."""
    return [
        {
            "citation": index,
            "id": chunk.id,
            "source": chunk.source,
            "title": chunk.title,
            "section": chunk.heading,
            "chunk_index": chunk.chunk_index,
            "score": chunk.score,
            "vector_score": chunk.vector_score,
            "lexical_score": chunk.lexical_score,
            "text": chunk.text,
        }
        for index, chunk in enumerate(chunks, start=1)
    ]
