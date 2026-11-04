from __future__ import annotations

import pytest

from src.config import Settings
from src.embeddings import HashingEmbedder
from src.retrieve import EmptyKnowledgeBaseError, Retriever, format_sources, lexical_score
from src.vector_store import SQLiteVectorStore, create_vector_store


def _retriever(settings: Settings) -> Retriever:
    embedder = HashingEmbedder()
    store = create_vector_store(settings, embedder)
    return Retriever(settings, store, embedder)


def test_retrieval_finds_pto_section(indexed_settings: Settings) -> None:
    retriever = _retriever(indexed_settings)
    chunks = retriever.retrieve("How many PTO days do employees get?")

    assert chunks
    assert chunks[0].source == "handbook.md"
    assert "20 days" in chunks[0].text
    assert chunks[0].score > 0


def test_retrieval_finds_security_section(indexed_settings: Settings) -> None:
    retriever = _retriever(indexed_settings)
    chunks = retriever.retrieve("What should I do if my laptop is stolen?")

    assert chunks
    assert chunks[0].source == "security.md"
    assert "one hour" in chunks[0].text


def test_empty_store_raises(settings: Settings) -> None:
    embedder = HashingEmbedder()
    store = SQLiteVectorStore(settings.vector_dir / "empty.sqlite3")
    retriever = Retriever(settings, store, embedder)
    with pytest.raises(EmptyKnowledgeBaseError):
        retriever.retrieve("Anything?")


def test_lexical_score_rewards_term_coverage() -> None:
    question = "What is the P1 response time?"
    relevant = "P1 Critical: first response time is 15 minutes."
    unrelated = "The marketing team publishes a monthly newsletter."

    assert lexical_score(question, relevant) > lexical_score(question, unrelated)


def test_format_sources_adds_one_based_citations(indexed_settings: Settings) -> None:
    retriever = _retriever(indexed_settings)
    sources = format_sources(retriever.retrieve("PTO", top_k=2))

    assert [source["citation"] for source in sources] == [1, 2]
    assert all(source["text"] for source in sources)
