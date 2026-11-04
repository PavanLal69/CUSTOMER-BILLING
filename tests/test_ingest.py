from __future__ import annotations

from pathlib import Path

import pytest

from src.config import Settings
from src.ingest import (
    DocumentReadError,
    LoadedDocument,
    chunk_document,
    ingest_directory,
    load_document,
    split_markdown_sections,
)
from src.embeddings import HashingEmbedder
from src.vector_store import SQLiteVectorStore


def test_chunking_preserves_section_metadata_and_overlap() -> None:
    text = "# Handbook\n\n## PTO\n\n" + ("Employees receive 20 days of PTO. " * 30)
    document = LoadedDocument(
        path=Path("handbook.md"),
        source="handbook.md",
        title="Handbook",
        text=text,
    )

    chunks = chunk_document(document, chunk_size=300, chunk_overlap=70)

    assert len(chunks) > 1
    assert all(chunk.source == "handbook.md" for chunk in chunks)
    assert all(chunk.heading == "Handbook > PTO" for chunk in chunks)
    assert all(chunk.metadata["char_count"] == len(chunk.text) for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))

    # Adjacent windows should share some text in addition to the repeated heading.
    assert any(chunks[index].text[-40:] in chunks[index + 1].text for index in range(len(chunks) - 1))


def test_markdown_sections_ignore_headings_inside_code_fences() -> None:
    text = """# Title

Intro.

```python
# This is a comment, not a heading.
print("hi")
```

## Real heading

Body.
"""
    sections = split_markdown_sections(text)
    headings = [heading for heading, _ in sections]
    assert "Title" in headings
    assert "Title > Real heading" in headings
    assert not any("This is a comment" in heading for heading in headings)


def test_load_document_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_document(tmp_path / "missing.md", data_dir=tmp_path)


def test_ingest_directory_persists_and_can_be_reloaded(settings: Settings) -> None:
    report = ingest_directory(settings, reset=True)

    assert report.documents == 2
    assert report.chunks > 0
    assert report.vector_backend == "sqlite"
    assert Path(report.store_location).exists()

    embedder = HashingEmbedder()
    store = SQLiteVectorStore(Path(report.store_location))
    assert store.count() == report.chunks
    assert len(store.list_sources()) == 2


def test_ingest_without_documents_raises(tmp_path: Path) -> None:
    data_dir = tmp_path / "empty"
    data_dir.mkdir()
    empty_settings = Settings(
        data_dir=data_dir,
        vector_dir=tmp_path / "vector",
        embedding_backend="hash",
        vector_backend="sqlite",
    )

    with pytest.raises(FileNotFoundError):
        ingest_directory(empty_settings)


def test_unsupported_document_type(tmp_path: Path) -> None:
    path = tmp_path / "notes.docx"
    path.write_text("not a markdown file", encoding="utf-8")
    with pytest.raises(DocumentReadError):
        load_document(path, data_dir=tmp_path)
