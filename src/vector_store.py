"""Persistent local vector stores.

ChromaDB is the recommended backend. A small SQLite + NumPy store is included as
a zero-extra-dependency fallback so the app still persists embeddings on a machine
where Chroma cannot be installed. Both stores expose the same small interface.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import re
import queue
import sqlite3
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class VectorRecord:
    """A chunk plus its embedding and scalar metadata."""

    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SearchHit:
    """A raw vector-store result."""

    id: str
    text: str
    metadata: dict[str, Any]
    score: float

    @property
    def source(self) -> str:
        return str(self.metadata.get("source", "unknown"))

    @property
    def title(self) -> str:
        return str(self.metadata.get("title", ""))

    @property
    def heading(self) -> str:
        return str(self.metadata.get("heading", ""))

    @property
    def chunk_index(self) -> int:
        try:
            return int(self.metadata.get("chunk_index", 0))
        except (TypeError, ValueError):
            return 0


class VectorStore(ABC):
    """Persistence interface used by ingestion and retrieval."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        ...

    @property
    @abstractmethod
    def location(self) -> str:
        ...

    @abstractmethod
    def count(self) -> int:
        ...

    @abstractmethod
    def add(self, records: list[VectorRecord]) -> int:
        ...

    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int) -> list[SearchHit]:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...

    @abstractmethod
    def list_sources(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def source_count(self) -> int:
        ...

    def close(self) -> None:
        """Release resources. Most backends do not keep a connection open."""


def _clean_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Keep only Chroma-compatible scalar metadata values."""
    clean: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = json.dumps(value, ensure_ascii=True)
    return clean


def _slug(value: str, *, max_length: int = 60) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return (value or "docs")[:max_length]


def artifact_slug(settings, embedder) -> str:
    """A stable artifact name that changes when the embedding model changes."""
    raw = f"{settings.collection_name}:{embedder.name}:{embedder.model_id}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]
    return f"{_slug(settings.collection_name, max_length=32)}-{_slug(embedder.name, max_length=20)}-{digest}"


class SQLiteVectorStore(VectorStore):
    """Persistent NumPy vector search backed by a single SQLite file.

    The sample corpus is tiny, so a full scan is fast and avoids a native
    dependency. The embeddings are stored as float32 BLOBs and scored with cosine
    similarity in NumPy.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connections: queue.LifoQueue[sqlite3.Connection] = queue.LifoQueue(maxsize=8)
        self._pool_slots = threading.BoundedSemaphore(8)
        self._closed = False
        self._init_schema()

    @property
    def backend_name(self) -> str:
        return "sqlite"

    @property
    def location(self) -> str:
        return str(self.path)

    @contextmanager
    def _connection(self):
        """Borrow an exclusive connection from the bounded SQLite pool."""
        self._pool_slots.acquire()
        try:
            connection = self._connections.get_nowait()
        except queue.Empty:
            try:
                connection = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
                connection.execute("PRAGMA busy_timeout = 30000")
            except Exception:
                self._pool_slots.release()
                raise
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if self._closed:
                connection.close()
            else:
                self._connections.put(connection)
            self._pool_slots.release()

    def close(self) -> None:
        self._closed = True
        while True:
            try:
                self._connections.get_nowait().close()
            except queue.Empty:
                break

    def _init_schema(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    heading TEXT NOT NULL DEFAULT '',
                    chunk_index INTEGER NOT NULL DEFAULT 0,
                    doc_id TEXT NOT NULL DEFAULT '',
                    content_hash TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    embedding BLOB NOT NULL,
                    dimension INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_source_title ON chunks(source, title)"
            )

    def count(self) -> int:
        with self._connection() as connection:
            row = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()
        return int(row[0]) if row else 0

    def add(self, records: list[VectorRecord]) -> int:
        if not records:
            return 0
        rows: list[tuple[Any, ...]] = []
        for record in records:
            vector = np.asarray(record.embedding, dtype=np.float32).reshape(-1)
            if vector.size == 0:
                raise ValueError(f"Empty embedding for chunk {record.id}")
            metadata = _clean_metadata(record.metadata)
            rows.append(
                (
                    record.id,
                    record.text,
                    str(metadata.get("source", "unknown")),
                    str(metadata.get("title", "")),
                    str(metadata.get("heading", "")),
                    int(metadata.get("chunk_index", 0)),
                    str(metadata.get("doc_id", "")),
                    str(metadata.get("content_hash", "")),
                    json.dumps(metadata, ensure_ascii=True),
                    vector.tobytes(),
                    int(vector.size),
                )
            )
        with self._connection() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO chunks
                (id, text, source, title, heading, chunk_index, doc_id, content_hash,
                 metadata_json, embedding, dimension)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchHit]:
        query = np.asarray(query_embedding, dtype=np.float32).reshape(-1)
        query_norm = float(np.linalg.norm(query))
        if query_norm == 0 or top_k <= 0:
            return []

        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, text, metadata_json, embedding, dimension
                FROM chunks
                """
            ).fetchall()

        scored: list[SearchHit] = []
        for chunk_id, text, metadata_json, blob, dimension in rows:
            if int(dimension) != query.size:
                continue
            vector = np.frombuffer(blob, dtype=np.float32)
            vector_norm = float(np.linalg.norm(vector))
            if vector_norm == 0:
                continue
            score = float(np.dot(query, vector) / (query_norm * vector_norm))
            metadata = json.loads(metadata_json) if metadata_json else {}
            scored.append(SearchHit(id=chunk_id, text=text, metadata=metadata, score=score))

        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[:top_k]

    def reset(self) -> None:
        with self._connection() as connection:
            connection.execute("DELETE FROM chunks")

    def list_sources(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT source, title, COUNT(*) AS chunks
                FROM chunks
                GROUP BY source, title
                ORDER BY source
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [{"source": row[0], "title": row[1], "chunks": int(row[2])} for row in rows]

    def source_count(self) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM (SELECT source, title FROM chunks GROUP BY source, title)"
            ).fetchone()
        return int(row[0]) if row else 0


class ChromaVectorStore(VectorStore):
    """ChromaDB persistent local collection using cosine distance."""

    def __init__(self, directory: Path, collection_name: str) -> None:
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "chromadb is not installed. Install requirements.txt or set VECTOR_BACKEND=sqlite."
            ) from exc

        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self._client = chromadb.PersistentClient(path=str(directory))
        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        return self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def backend_name(self) -> str:
        return "chroma"

    @property
    def location(self) -> str:
        return str(self.directory)

    def count(self) -> int:
        try:
            return int(self._collection.count())
        except Exception:  # pragma: no cover - Chroma internals vary by version
            return 0

    def add(self, records: list[VectorRecord]) -> int:
        if not records:
            return 0
        try:
            self._collection.upsert(
                ids=[record.id for record in records],
                documents=[record.text for record in records],
                metadatas=[_clean_metadata(record.metadata) for record in records],
                embeddings=[record.embedding for record in records],
            )
        except Exception as exc:  # pragma: no cover - depends on Chroma version
            raise RuntimeError(
                "ChromaDB rejected the embeddings. This usually means the collection "
                "was created with a different embedding dimension. Run ingestion with "
                "--reset, or delete vector_store/chroma."
            ) from exc
        return len(records)

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchHit]:
        total = self.count()
        if total == 0 or top_k <= 0:
            return []
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, total),
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        hits: list[SearchHit] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            # The collection is configured with cosine space, so distance = 1 - cosine.
            score = 1.0 - float(distance)
            hits.append(
                SearchHit(
                    id=str(chunk_id),
                    text=str(text or ""),
                    metadata=dict(metadata or {}),
                    score=score,
                )
            )
        return hits

    def reset(self) -> None:
        try:
            self._client.delete_collection(self.collection_name)
        except Exception:  # pragma: no cover - collection may already be gone
            LOGGER.debug("Chroma collection %s did not exist during reset", self.collection_name)
        self._collection = self._get_or_create_collection()

    def list_sources(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        try:
            result = self._collection.get(include=["metadatas"], limit=100_000)
        except Exception:  # pragma: no cover
            return []
        counts: dict[tuple[str, str], int] = {}
        for metadata in result.get("metadatas") or []:
            metadata = metadata or {}
            key = (str(metadata.get("source", "unknown")), str(metadata.get("title", "")))
            counts[key] = counts.get(key, 0) + 1
        rows = [
            {"source": source, "title": title, "chunks": chunks}
            for (source, title), chunks in sorted(counts.items())
        ]
        return rows[offset : offset + limit]

    def source_count(self) -> int:
        return len(self.list_sources(limit=100_000))


def create_vector_store(settings, embedder) -> VectorStore:
    """Create the configured persistent store, falling back to SQLite in auto mode."""
    backend = settings.vector_backend.strip().lower()
    slug = artifact_slug(settings, embedder)

    if backend in {"sqlite", "sqlite3"}:
        return SQLiteVectorStore(settings.vector_dir / f"rag-{slug}.sqlite3")

    if backend in {"chroma", "chromadb"}:
        if importlib.util.find_spec("chromadb") is None:
            raise RuntimeError(
                "VECTOR_BACKEND=chroma requires chromadb. Install requirements.txt "
                "or set VECTOR_BACKEND=sqlite."
            )
        return ChromaVectorStore(settings.vector_dir / "chroma", slug)

    if backend == "auto":
        if importlib.util.find_spec("chromadb") is not None:
            try:
                LOGGER.info("Using ChromaDB persistent vector store")
                return ChromaVectorStore(settings.vector_dir / "chroma", slug)
            except Exception as exc:  # pragma: no cover - environment dependent
                LOGGER.warning("ChromaDB unavailable (%s); falling back to SQLite", exc)
        else:
            LOGGER.warning(
                "chromadb is not installed; using the persistent SQLite vector store. "
                "Install requirements.txt for the recommended Chroma backend."
            )
        return SQLiteVectorStore(settings.vector_dir / f"rag-{slug}.sqlite3")

    raise ValueError(
        f"Unknown VECTOR_BACKEND={settings.vector_backend!r}. Use auto, chroma, or sqlite."
    )
