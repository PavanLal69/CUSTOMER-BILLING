"""FastAPI application exposing the RAG pipeline.

Run locally:
    python -m uvicorn src.main:app --reload
    python -m src.main
"""

from __future__ import annotations

import logging
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from src import __version__
from src.config import Settings
from src.embeddings import create_embedder
from src.generate import GroundedGenerator
from src.ingest import IngestReport, ingest_directory
from src.retrieve import EmptyKnowledgeBaseError, Retriever, format_sources
from src.vector_store import create_vector_store

LOGGER = logging.getLogger(__name__)
_otel_provider_configured = False

FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"


# ---------------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"question": "How many PTO days do employees get?", "top_k": 4}
        }
    )

    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural-language question about the internal knowledge base.",
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Optional number of chunks to retrieve; defaults to TOP_K.",
    )


class SourceOut(BaseModel):
    citation: int = Field(description="1-based citation number used in the answer.")
    id: str
    source: str
    title: str
    section: str
    chunk_index: int
    score: float
    vector_score: float
    lexical_score: float
    cited: bool
    text: str = Field(description="The retrieved chunk text, including its heading.")


class CitationOut(BaseModel):
    index: int
    source: str
    title: str
    section: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[CitationOut]
    sources: list[SourceOut]
    model: str
    mode: str
    latency_ms: float
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    ready: bool
    chunks: int
    documents: int
    embedding_backend: str
    embedding_model: str
    vector_backend: str
    vector_store: str
    llm_provider: str
    llm_model: str
    version: str


class SourceListResponse(BaseModel):
    count: int
    total: int
    limit: int
    offset: int
    sources: list[dict[str, Any]]


class WebVitalEvent(BaseModel):
    name: str = Field(pattern=r"^(CLS|INP|LCP|TTFB)$")
    value: float = Field(ge=0, le=600_000)
    rating: str = Field(pattern=r"^(good|needs-improvement|poor)$")
    id: str = Field(min_length=1, max_length=100)
    navigationType: str = Field(max_length=40)


class IngestRequest(BaseModel):
    reset: bool = Field(
        default=True,
        description="Clear the collection before indexing. Keep true for a clean rebuild.",
    )


class IngestResponse(BaseModel):
    documents: int
    chunks: int
    embedding_backend: str
    embedding_model: str
    vector_backend: str
    store_location: str
    elapsed_ms: float
    reset: bool
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Service layer
# ---------------------------------------------------------------------------


class RAGService:
    """Owns the embedder, vector store, retriever, and generator."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedder = create_embedder(settings)
        self.store = create_vector_store(settings, self.embedder)
        self.retriever = Retriever(settings, self.store, self.embedder)
        self.generator = GroundedGenerator(settings)

    def answer(self, question: str, *, top_k: int | None = None) -> QueryResponse:
        started = time.perf_counter()
        chunks = self.retriever.retrieve(question, top_k=top_k)
        generated = self.generator.generate(question, chunks)

        sources = format_sources(chunks)
        cited_numbers = set(generated.citations)
        for source in sources:
            source["cited"] = source["citation"] in cited_numbers

        by_index = {source["citation"]: source for source in sources}
        citation_details = [
            CitationOut(
                index=number,
                source=by_index[number]["source"],
                title=by_index[number]["title"],
                section=by_index[number]["section"],
            )
            for number in generated.citations
            if number in by_index
        ]

        return QueryResponse(
            question=question.strip(),
            answer=generated.text,
            citations=citation_details,
            sources=sources,
            model=generated.model,
            mode=generated.mode,
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
            warnings=generated.warnings,
        )

    def ingest(self, *, reset: bool = True) -> IngestResponse:
        report: IngestReport = ingest_directory(
            self.settings,
            reset=reset,
            embedder=self.embedder,
            store=self.store,
        )
        return IngestResponse(**report.as_dict())

    def health(self) -> HealthResponse:
        try:
            chunks = self.store.count()
            source_count = self.store.source_count()
        except Exception:  # A broken store should surface as "not ready", not a 500.
            LOGGER.exception("Could not read vector-store health")
            chunks = 0
            source_count = 0
        return HealthResponse(
            status="ok",
            ready=chunks > 0,
            chunks=chunks,
            documents=source_count,
            embedding_backend=self.embedder.name,
            embedding_model=self.embedder.model_id,
            vector_backend=self.store.backend_name,
            vector_store=self.store.location,
            llm_provider=self.generator.provider,
            llm_model=self.generator.model,
            version=__version__,
        )


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app(settings: Settings | None = None) -> FastAPI:
    global _otel_provider_configured
    resolved_settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.basicConfig(
            level=getattr(logging, resolved_settings.log_level, logging.INFO),
            format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        )
        LOGGER.info(
            "Starting RAG API (embeddings=%s, vector=%s, llm=%s)",
            resolved_settings.embedding_backend,
            resolved_settings.vector_backend,
            resolved_settings.resolved_llm_provider,
        )
        app.state.service = RAGService(resolved_settings)
        try:
            yield
        finally:
            app.state.service.store.close()

    app = FastAPI(
        title="Northstar Labs RAG Knowledge Assistant",
        version=__version__,
        description=(
            "Retrieval-augmented question answering over the internal Northstar Labs "
            "handbook, security policy, travel policy, support playbook, and product FAQ. "
            "Answers include validated citations and the retrieved source texts."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=5)

    @app.middleware("http")
    async def performance_headers(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.1f}"
        if request.url.path.startswith("/app/"):
            asset_name = Path(request.url.path).name
            hashed_asset = bool(re.search(r"-[A-Za-z0-9_-]{8,}\.", asset_name))
            response.headers["Cache-Control"] = (
                "public, max-age=31536000, immutable" if hashed_asset else "no-cache"
            )
        if elapsed_ms >= 500:
            LOGGER.info(
                "slow_request method=%s path=%s status=%s duration_ms=%.1f",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
        return response

    if os.getenv("OTEL_ENABLED", "false").lower() in {"1", "true", "yes"}:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

            if not _otel_provider_configured:
                traces_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
                has_otlp_endpoint = traces_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
                if traces_endpoint:
                    exporter = OTLPSpanExporter(endpoint=traces_endpoint)
                elif has_otlp_endpoint:
                    exporter = OTLPSpanExporter()
                else:
                    exporter = ConsoleSpanExporter()
                provider = TracerProvider(
                    resource=Resource.create(
                        {"service.name": os.getenv("OTEL_SERVICE_NAME", "northstar-rag-api")}
                    )
                )
                provider.add_span_processor(BatchSpanProcessor(exporter))
                trace.set_tracer_provider(provider)
                _otel_provider_configured = True
            FastAPIInstrumentor.instrument_app(app)
        except ImportError:
            LOGGER.warning(
                "OTEL_ENABLED is set but OpenTelemetry instrumentation is not installed"
            )

    @app.exception_handler(EmptyKnowledgeBaseError)
    async def empty_store_handler(_: Request, exc: EmptyKnowledgeBaseError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": str(exc),
                "hint": "POST /ingest or run `python -m src.ingest` first.",
            },
        )

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": "Northstar Labs RAG Knowledge Assistant",
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
            "query": "POST /query",
            "ingest": "POST /ingest",
        }
        if FRONTEND_DIST.exists():
            payload["ui"] = "/app/"
        return payload

    @app.get("/health", response_model=HealthResponse, tags=["operations"])
    def health(request: Request) -> HealthResponse:
        return request.app.state.service.health()

    @app.get("/sources", response_model=SourceListResponse, tags=["knowledge base"])
    def list_sources(
        request: Request,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> SourceListResponse:
        store = request.app.state.service.store
        sources = store.list_sources(limit=limit, offset=offset)
        return SourceListResponse(
            count=len(sources), total=store.source_count(), limit=limit, offset=offset, sources=sources
        )

    @app.post("/metrics/web-vitals", status_code=202, include_in_schema=False)
    def receive_web_vitals(event: WebVitalEvent) -> dict[str, str]:
        LOGGER.info(
            "web_vital name=%s value=%s rating=%s navigation=%s event_id=%s",
            event.name,
            event.value,
            event.rating,
            event.navigationType,
            event.id,
        )
        return {"status": "accepted"}

    @app.post("/query", response_model=QueryResponse, tags=["rag"])
    def query(payload: QueryRequest, request: Request) -> QueryResponse:
        if not payload.question.strip():
            raise HTTPException(status_code=422, detail="question must not be blank")
        return request.app.state.service.answer(payload.question, top_k=payload.top_k)

    @app.post("/ingest", response_model=IngestResponse, tags=["knowledge base"])
    def ingest(payload: IngestRequest, request: Request) -> IngestResponse:
        try:
            return request.app.state.service.ingest(reset=payload.reset)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            LOGGER.exception("Ingestion endpoint failed")
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    if FRONTEND_DIST.exists():
        app.mount("/app", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        log_level="info",
    )
