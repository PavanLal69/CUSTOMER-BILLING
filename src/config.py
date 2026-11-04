"""Application configuration loaded from environment variables.

The module deliberately avoids a heavy settings framework. A frozen dataclass is
enough for this project and keeps the dependency surface small.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load a local .env when present. Real environment variables take precedence.
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_PROVIDER_DEFAULTS: dict[str, tuple[str, str | None]] = {
    "deepseek": ("deepseek-chat", "https://api.deepseek.com/v1"),
    "openai": ("gpt-4o-mini", "https://api.openai.com/v1"),
    "ollama": ("llama3.2", "http://localhost:11434/v1"),
}


def _env(name: str, default: str | None = None) -> str | None:
    """Return a stripped environment value, treating blanks as unset."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _env_float(name: str, default: float) -> float:
    raw = _env(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc


def _resolve_path(raw: str, *, default: str) -> Path:
    """Resolve a path relative to the repository root, not the shell cwd."""
    value = Path(raw or default).expanduser()
    if not value.is_absolute():
        value = PROJECT_ROOT / value
    return value.resolve()


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration.

    ``auto`` is the default for both embedding and vector backends so the app can
    start on a machine without the optional heavy dependencies. Production users
    should install ``requirements.txt`` and pin explicit backends.
    """

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data" / "sample_docs"
    vector_dir: Path = PROJECT_ROOT / "vector_store"

    chunk_size: int = 900
    chunk_overlap: int = 150
    embedding_batch_size: int = 32

    top_k: int = 4
    retrieval_candidates: int = 12
    min_retrieval_score: float = 0.0

    embedding_backend: str = "auto"
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    vector_backend: str = "auto"
    collection_name: str = "northstar_docs"

    llm_provider: str = "auto"
    llm_model: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = field(default=None, repr=False)
    deepseek_api_key: str | None = field(default=None, repr=False)
    openai_api_key: str | None = field(default=None, repr=False)
    llm_temperature: float = 0.0
    llm_timeout_seconds: float = 60.0
    llm_max_tokens: int = 700

    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if self.chunk_size < 100:
            raise ValueError("CHUNK_SIZE must be at least 100 characters")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be >= 0 and smaller than CHUNK_SIZE")
        if not 1 <= self.top_k <= 20:
            raise ValueError("TOP_K must be between 1 and 20")
        if self.retrieval_candidates < self.top_k:
            raise ValueError("RETRIEVAL_CANDIDATES must be >= TOP_K")
        if not 0.0 <= self.llm_temperature <= 2.0:
            raise ValueError("LLM_TEMPERATURE must be between 0 and 2")

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from the process environment / .env file."""
        data_dir = _resolve_path(_env("DATA_DIR") or "data/sample_docs", default="data/sample_docs")
        vector_dir = _resolve_path(_env("VECTOR_DIR") or "vector_store", default="vector_store")
        return cls(
            data_dir=data_dir,
            vector_dir=vector_dir,
            chunk_size=_env_int("CHUNK_SIZE", 900),
            chunk_overlap=_env_int("CHUNK_OVERLAP", 150),
            embedding_batch_size=_env_int("EMBEDDING_BATCH_SIZE", 32),
            top_k=_env_int("TOP_K", 4),
            retrieval_candidates=_env_int("RETRIEVAL_CANDIDATES", 12),
            min_retrieval_score=_env_float("MIN_RETRIEVAL_SCORE", 0.0),
            embedding_backend=(_env("EMBEDDING_BACKEND", "auto") or "auto").lower(),
            embedding_model=_env("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
            or DEFAULT_EMBEDDING_MODEL,
            vector_backend=(_env("VECTOR_BACKEND", "auto") or "auto").lower(),
            collection_name=_env("COLLECTION_NAME", "northstar_docs") or "northstar_docs",
            llm_provider=(_env("LLM_PROVIDER", "auto") or "auto").lower(),
            llm_model=_env("LLM_MODEL"),
            llm_base_url=_env("LLM_BASE_URL"),
            llm_api_key=_env("LLM_API_KEY"),
            deepseek_api_key=_env("DEEPSEEK_API_KEY"),
            openai_api_key=_env("OPENAI_API_KEY"),
            llm_temperature=_env_float("LLM_TEMPERATURE", 0.0),
            llm_timeout_seconds=_env_float("LLM_TIMEOUT_SECONDS", 60.0),
            llm_max_tokens=_env_int("LLM_MAX_TOKENS", 700),
            log_level=(_env("LOG_LEVEL", "INFO") or "INFO").upper(),
        )

    def with_overrides(self, **overrides: Any) -> "Settings":
        """Return a validated copy with a few fields replaced (useful in tests)."""
        return replace(self, **overrides)

    @property
    def resolved_llm_provider(self) -> str:
        """Resolve ``auto`` to a concrete provider based on available credentials."""
        provider = self.llm_provider.strip().lower()
        if provider != "auto":
            return provider
        if self.deepseek_api_key:
            return "deepseek"
        if self.openai_api_key:
            return "openai"
        if self.llm_api_key and self.llm_base_url:
            return "custom"
        return "offline"

    @property
    def effective_llm_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        return _PROVIDER_DEFAULTS.get(self.resolved_llm_provider, ("offline-extractive", None))[0]

    @property
    def effective_llm_base_url(self) -> str | None:
        if self.llm_base_url:
            return self.llm_base_url.rstrip("/")
        return _PROVIDER_DEFAULTS.get(self.resolved_llm_provider, (None, None))[1]

    def api_key_for(self, provider: str | None = None) -> str | None:
        """Return the most specific API key for a provider."""
        provider = (provider or self.resolved_llm_provider).lower()
        if self.llm_api_key:
            return self.llm_api_key
        if provider == "deepseek":
            return self.deepseek_api_key
        if provider == "openai":
            return self.openai_api_key
        return None

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_dir.mkdir(parents=True, exist_ok=True)
