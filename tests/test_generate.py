from __future__ import annotations

from src.config import Settings
from src.generate import (
    GroundedGenerator,
    build_messages,
    parse_citations,
)
from src.retrieve import RetrievedChunk


def _chunk(text: str, *, heading: str = "Handbook > PTO", index: int = 0) -> RetrievedChunk:
    return RetrievedChunk(
        id=f"chunk-{index}",
        text=text,
        source="handbook.md",
        title="Handbook",
        heading=heading,
        chunk_index=index,
        score=0.9,
        vector_score=0.8,
        lexical_score=0.7,
        metadata={"source": "handbook.md", "title": "Handbook", "heading": heading},
    )


def test_prompt_numbers_sources_and_contains_question() -> None:
    chunks = [
        _chunk("Employees receive 20 days of PTO."),
        _chunk("Parental leave is 16 weeks.", heading="Handbook > Parental leave", index=1),
    ]
    messages = build_messages("How much PTO is there?", chunks)

    assert messages[0]["role"] == "system"
    assert "ONLY" in messages[0]["content"]
    assert "[1] Source: handbook.md" in messages[1]["content"]
    assert "[2] Source: handbook.md" in messages[1]["content"]
    assert "How much PTO is there?" in messages[1]["content"]


def test_citation_parser_accepts_groups_and_flags_out_of_range() -> None:
    valid, invalid = parse_citations("Answer [1] and [2, 1] but not [7].", max_source=2)
    assert valid == [1, 2]
    assert invalid == [7]


def test_offline_generator_returns_cited_answer() -> None:
    settings = Settings(llm_provider="offline", embedding_backend="hash", vector_backend="sqlite")
    generator = GroundedGenerator(settings)
    chunks = [_chunk("Eligible employees receive 20 days of paid time off (PTO) per calendar year.")]

    answer = generator.generate("How many PTO days do employees get?", chunks)

    assert answer.mode == "offline-extractive"
    assert "[1]" in answer.text
    assert answer.citations == [1]


def test_offline_generator_refuses_without_query_overlap() -> None:
    settings = Settings(llm_provider="offline", embedding_backend="hash", vector_backend="sqlite")
    generator = GroundedGenerator(settings)
    chunks = [_chunk("The cafeteria opens at 08:00 and closes at 17:00.")]

    answer = generator.generate("What is the quantum entanglement policy?", chunks)

    assert answer.citations == []
    assert "couldn't find" in answer.text.lower()
