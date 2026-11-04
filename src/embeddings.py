"""Embedding backends.

The production path uses a local Sentence Transformers model (a Hugging Face
model downloaded once and cached on disk). The hashing backend is a deterministic
fallback for offline environments and CI; it is lexical rather than semantic, but
it keeps ingestion, retrieval, the API, and tests fully operational without a
network connection.
"""

from __future__ import annotations

import hashlib
import importlib.util
import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

import numpy as np

LOGGER = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#._'-]*")

_STOPWORDS = frozenset(
    """
    a an and are as at be been being but by can could did do does doing for from
    get gets got had has have having he her here hers him his how i if in into is
    it its just me more most my no not of on or our ours out over own same she
    should so some such than that the their theirs them then there these they
    this those to too under up us very was we were what when where which while
    who whom why will with would you your yours
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer used by the fallback embedder and lexical rerank."""
    return _TOKEN_RE.findall(text.lower())


def content_tokens(text: str) -> list[str]:
    """Return tokens with common English stopwords removed."""
    return [token for token in tokenize(text) if token not in _STOPWORDS and len(token) > 1]


class Embedder(ABC):
    """Small interface shared by all embedding backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable backend name used in vector-store artifact names."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Human-readable model identifier."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of documents."""

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query. Backends may override this for efficiency."""
        return self.embed_documents([text])[0]


class HashingEmbedder(Embedder):
    """Deterministic feature-hashing embedder with word, bigram, and char features.

    This is not a neural model. It exists so the project works offline and so the
    test suite never depends on downloading a model. The hybrid lexical reranker in
    ``retrieve.py`` compensates for some of its limitations.
    """

    def __init__(self, dimension: int = 768) -> None:
        if dimension < 64:
            raise ValueError("Hashing dimension must be at least 64")
        self._dimension = dimension

    @property
    def name(self) -> str:
        return "hash"

    @property
    def model_id(self) -> str:
        return f"hash-ngrams-{self._dimension}"

    @property
    def dimension(self) -> int:
        return self._dimension

    @staticmethod
    def _feature_vector(text: str, dimension: int) -> np.ndarray:
        vector = np.zeros(dimension, dtype=np.float32)
        tokens = tokenize(text)
        content = [token for token in tokens if token not in _STOPWORDS and len(token) > 1]

        features: list[tuple[str, float]] = []
        for index, token in enumerate(content):
            features.append((f"w:{token}", 1.0))
            if index + 1 < len(content):
                features.append((f"b:{token}_{content[index + 1]}", 0.65))
            if len(token) >= 5:
                padded = f"^{token}$"
                for start in range(len(padded) - 3):
                    features.append((f"c:{padded[start:start + 4]}", 0.22))

        for feature, weight in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "little") % dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[bucket] += sign * weight

        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm
        else:
            # A zero vector is invalid for cosine search; keep a tiny deterministic
            # direction so empty/degenerate text is still representable.
            vector[0] = 1.0
        return vector

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._feature_vector(text, self._dimension).tolist() for text in texts]


class SentenceTransformerEmbedder(Embedder):
    """Local Hugging Face embedding model loaded through Sentence Transformers.

    The model is loaded lazily so importing the app or running unit tests with the
    hashing backend does not trigger a download.
    """

    def __init__(self, model_id: str, *, device: str | None = None, batch_size: int = 32) -> None:
        self._model_id = model_id
        self._device = device
        self._batch_size = batch_size
        self._model = None

    @property
    def name(self) -> str:
        return "sentence-transformers"

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimension(self) -> int:
        model = self._load()
        dimension = model.get_sentence_embedding_dimension()
        if dimension is None:
            raise RuntimeError(f"Could not determine embedding dimension for {self._model_id}")
        return int(dimension)

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "sentence-transformers is not installed. Run "
                "`pip install -r requirements.txt`, or set EMBEDDING_BACKEND=hash "
                "for the offline fallback."
            ) from exc

        LOGGER.info("Loading embedding model %s (first run may download it)", self._model_id)
        try:
            self._model = SentenceTransformer(self._model_id, device=self._device)
        except Exception as exc:  # pragma: no cover - network/model dependent
            raise RuntimeError(
                f"Could not load embedding model {self._model_id!r}. Check network access "
                "to Hugging Face, or set EMBEDDING_BACKEND=hash for an offline fallback."
            ) from exc
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(
            list(texts),
            batch_size=self._batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return np.asarray(vectors, dtype=np.float32).tolist()


def create_embedder(settings) -> Embedder:
    """Create the embedding backend selected by configuration.

    ``auto`` prefers Sentence Transformers when the package is importable. It does
    not attempt to download the model during app startup.
    """
    backend = settings.embedding_backend.strip().lower()

    if backend in {"hash", "hashing", "fallback"}:
        return HashingEmbedder()

    if backend in {"sentence-transformers", "sentence_transformers", "st", "hf", "huggingface"}:
        if importlib.util.find_spec("sentence_transformers") is None:
            raise RuntimeError(
                "EMBEDDING_BACKEND=sentence-transformers requires the "
                "sentence-transformers package. Install requirements.txt or use "
                "EMBEDDING_BACKEND=hash."
            )
        return SentenceTransformerEmbedder(
            settings.embedding_model,
            batch_size=settings.embedding_batch_size,
        )

    if backend == "auto":
        if importlib.util.find_spec("sentence_transformers") is not None:
            LOGGER.info("Using Sentence Transformers embedding model %s", settings.embedding_model)
            return SentenceTransformerEmbedder(
                settings.embedding_model,
                batch_size=settings.embedding_batch_size,
            )
        LOGGER.warning(
            "sentence-transformers is not installed; using deterministic hashing "
            "embeddings. Install requirements.txt for semantic retrieval."
        )
        return HashingEmbedder()

    raise ValueError(
        f"Unknown EMBEDDING_BACKEND={settings.embedding_backend!r}. "
        "Use auto, sentence-transformers, or hash."
    )
