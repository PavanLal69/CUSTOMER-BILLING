"""Document ingestion: markdown-aware chunking, embedding, and persistence.

Run as a module:
    python -m src.ingest

Or directly:
    python src/ingest.py --reset
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # Support `python src/ingest.py`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import Settings
from src.embeddings import Embedder, create_embedder
from src.vector_store import VectorRecord, VectorStore, create_vector_store

LOGGER = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".pdf"}
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass(slots=True)
class LoadedDocument:
    path: Path
    source: str
    title: str
    text: str


@dataclass(slots=True)
class TextChunk:
    id: str
    text: str
    source: str
    title: str
    heading: str
    chunk_index: int
    doc_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self, embedding: list[float]) -> VectorRecord:
        return VectorRecord(
            id=self.id,
            text=self.text,
            embedding=embedding,
            metadata=self.metadata,
        )


@dataclass(slots=True)
class IngestReport:
    documents: int
    chunks: int
    embedding_backend: str
    embedding_model: str
    vector_backend: str
    store_location: str
    elapsed_ms: float
    reset: bool
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class DocumentReadError(RuntimeError):
    """Raised when an input document cannot be parsed."""


def normalize_text(text: str) -> str:
    """Normalize line endings/whitespace without destroying paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    return text[end + 4 :].lstrip("\n")


def extract_title(text: str, fallback: str) -> str:
    match = _H1_RE.search(text)
    if match:
        return match.group(1).strip()
    return fallback


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into ``(heading_path, body)`` sections.

    Headings are tracked in a stack so a chunk knows its full section path, e.g.
    ``"Employee Handbook > 3. Paid time off"``. Headings inside fenced code blocks
    are ignored.
    """
    lines = text.splitlines()
    sections: list[tuple[str, str]] = []
    heading_stack: list[tuple[int, str]] = []
    body: list[str] = []
    heading_path = ""
    in_code_fence = False

    def flush() -> None:
        nonlocal body
        section_body = "\n".join(body).strip()
        if section_body:
            sections.append((heading_path, section_body))
        body = []

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            body.append(line)
            continue

        match = None if in_code_fence else _HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            heading = match.group(2).strip()
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, heading))
            heading_path = " > ".join(value for _, value in heading_stack)
            continue

        body.append(line)

    flush()
    return sections


def _window_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping character windows aligned to natural breaks."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    windows: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        hard_end = min(start + size, length)
        end = hard_end

        if hard_end < length:
            window = text[start:hard_end]
            floor = max(40, int(size * 0.55))
            for separator in ("\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "):
                index = window.rfind(separator)
                if index >= floor:
                    end = start + index + len(separator)
                    break

        chunk = text[start:end].strip()
        if chunk:
            windows.append(chunk)
        if end >= length:
            break

        next_start = max(end - overlap, start + 1)
        # Do not begin the overlap in the middle of a word.
        while (
            next_start < end
            and next_start > 0
            and text[next_start - 1].isalnum()
            and text[next_start].isalnum()
        ):
            next_start += 1
        start = next_start

    return windows


def _make_chunk_id(doc_id: str, chunk_index: int, content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    return f"{doc_id[:16]}-{chunk_index:04d}-{digest}"


def chunk_document(
    document: LoadedDocument,
    *,
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> list[TextChunk]:
    """Chunk one document and attach citation-friendly metadata."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = _strip_frontmatter(normalize_text(document.text))
    sections = split_markdown_sections(text)
    if not sections:
        sections = [(document.title, text)]

    doc_id = hashlib.sha256(document.source.encode("utf-8")).hexdigest()[:24]
    chunks: list[TextChunk] = []
    chunk_index = 0

    for heading, body in sections:
        prefix = f"{heading}\n\n" if heading else ""
        effective_size = max(150, chunk_size - len(prefix))
        effective_overlap = min(chunk_overlap, max(20, effective_size // 3))

        for window in _window_text(body, effective_size, effective_overlap):
            content = f"{prefix}{window}".strip()
            if not content:
                continue
            metadata = {
                "source": document.source,
                "title": document.title,
                "heading": heading or document.title,
                "chunk_index": chunk_index,
                "doc_id": doc_id,
                "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "char_count": len(content),
            }
            chunks.append(
                TextChunk(
                    id=_make_chunk_id(doc_id, chunk_index, content),
                    text=content,
                    source=document.source,
                    title=document.title,
                    heading=heading or document.title,
                    chunk_index=chunk_index,
                    doc_id=doc_id,
                    metadata=metadata,
                )
            )
            chunk_index += 1

    return chunks


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise DocumentReadError(
            f"Cannot read {path.name}: install pypdf (`pip install pypdf`) or convert "
            "the PDF to Markdown."
        ) from exc

    try:
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as exc:
        raise DocumentReadError(f"Could not parse PDF {path.name}: {exc}") from exc
    text = "\n\n".join(page for page in pages if page)
    if not text:
        raise DocumentReadError(f"PDF {path.name} did not contain extractable text")
    return text


def load_document(path: Path, *, data_dir: Path) -> LoadedDocument:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DocumentReadError(f"Unsupported document type: {path.suffix}")

    try:
        if suffix == ".pdf":
            text = _read_pdf(path)
        else:
            text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentReadError(f"{path.name} is not valid UTF-8 text") from exc

    text = normalize_text(text)
    if not text:
        raise DocumentReadError(f"{path.name} is empty")

    source = path.relative_to(data_dir).as_posix()
    return LoadedDocument(
        path=path,
        source=source,
        title=extract_title(text, path.stem.replace("-", " ").replace("_", " ").title()),
        text=text,
    )


def find_document_paths(data_dir: Path) -> list[Path]:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")
    paths = [
        path
        for path in data_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not any(part.startswith(".") for part in path.relative_to(data_dir).parts)
    ]
    return sorted(paths)


def load_documents(data_dir: Path) -> list[LoadedDocument]:
    paths = find_document_paths(data_dir)
    if not paths:
        raise FileNotFoundError(
            f"No supported documents found in {data_dir}. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    return [load_document(path, data_dir=data_dir) for path in paths]


def ingest_directory(
    settings: Settings,
    *,
    reset: bool = True,
    embedder: Embedder | None = None,
    store: VectorStore | None = None,
) -> IngestReport:
    """Load, chunk, embed, and persist every supported document in ``data_dir``."""
    started = time.perf_counter()
    settings.ensure_directories()
    warnings: list[str] = []

    documents = load_documents(settings.data_dir)
    chunks: list[TextChunk] = []
    for document in documents:
        document_chunks = chunk_document(
            document,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        chunks.extend(document_chunks)
        LOGGER.info("Chunked %s into %d chunks", document.source, len(document_chunks))

    if not chunks:
        raise ValueError("Documents were loaded but produced no text chunks")

    embedder = embedder or create_embedder(settings)
    store = store or create_vector_store(settings, embedder)
    if reset:
        store.reset()

    LOGGER.info(
        "Embedding %d chunks with %s (%s)",
        len(chunks),
        embedder.name,
        embedder.model_id,
    )
    embeddings: list[list[float]] = []
    batch_size = max(1, settings.embedding_batch_size)
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        embeddings.extend(embedder.embed_documents([chunk.text for chunk in batch]))
        LOGGER.debug("Embedded %d/%d chunks", min(start + batch_size, len(chunks)), len(chunks))

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            f"Embedding backend returned {len(embeddings)} vectors for {len(chunks)} chunks"
        )

    records = [
        chunk.to_record(embedding) for chunk, embedding in zip(chunks, embeddings, strict=True)
    ]
    store.add(records)

    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    report = IngestReport(
        documents=len(documents),
        chunks=len(records),
        embedding_backend=embedder.name,
        embedding_model=embedder.model_id,
        vector_backend=store.backend_name,
        store_location=store.location,
        elapsed_ms=elapsed_ms,
        reset=reset,
        warnings=warnings,
    )
    LOGGER.info(
        "Indexed %d chunks from %d documents in %.1f ms (%s + %s)",
        report.chunks,
        report.documents,
        report.elapsed_ms,
        report.embedding_backend,
        report.vector_backend,
    )
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Chunk and embed the sample knowledge base into a local vector store."
    )
    parser.add_argument("--data-dir", type=Path, help="Directory containing .md/.txt/.pdf files")
    parser.add_argument("--vector-dir", type=Path, help="Directory for persistent store artifacts")
    parser.add_argument("--chunk-size", type=int, help="Target chunk size in characters")
    parser.add_argument("--chunk-overlap", type=int, help="Overlap between adjacent chunks")
    parser.add_argument(
        "--embedding-backend",
        choices=["auto", "sentence-transformers", "hash"],
        help="Embedding backend override",
    )
    parser.add_argument(
        "--vector-backend",
        choices=["auto", "chroma", "sqlite"],
        help="Vector store backend override",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Append/upsert instead of clearing the existing collection first",
    )
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()

    overrides: dict[str, Any] = {}
    if args.data_dir:
        overrides["data_dir"] = args.data_dir.resolve()
    if args.vector_dir:
        overrides["vector_dir"] = args.vector_dir.resolve()
    if args.chunk_size:
        overrides["chunk_size"] = args.chunk_size
    if args.chunk_overlap is not None:
        overrides["chunk_overlap"] = args.chunk_overlap
    if args.embedding_backend:
        overrides["embedding_backend"] = args.embedding_backend
    if args.vector_backend:
        overrides["vector_backend"] = args.vector_backend

    if overrides:
        settings = settings.with_overrides(**overrides)

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    try:
        report = ingest_directory(settings, reset=not args.no_reset)
    except Exception as exc:
        print(f"Ingestion failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(
            f"Ingested {report.chunks} chunks from {report.documents} documents "
            f"in {report.elapsed_ms:.1f} ms"
        )
        print(
            f"Embeddings: {report.embedding_model} ({report.embedding_backend}) | "
            f"Store: {report.vector_backend} at {report.store_location}"
        )
        print("Start the API with: python -m uvicorn src.main:app --reload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
