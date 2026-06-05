import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.appointments_router import router as appointments_router
from src.api.attachments_router import router as attachments_router
from src.config import get_settings
from src.db.session import init_db
from src.frontend_static import register_production_frontend
from src.lab_results_rag import init_lab_results_chain
from src.logging_config import configure_logging
from src.mental_health_rag import init_mental_health_chain
from src.middleware.rate_limit import InMemoryRateLimiter, RateLimitMiddleware
from src.middleware.request_context import RequestContextMiddleware
from src.mock import mock_router
from src.rag import ensure_rag_chain, init_rag_chain, invoke_rag, is_rag_ready
from src.schemas import ChatRequest, ChatResponse, HealthResponse

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent


def _should_eager_load_rag(*, load_rag_on_startup: bool) -> bool:
    if not load_rag_on_startup:
        return False
    if os.getenv("SKIP_RAG_ON_STARTUP", "").lower() in ("1", "true", "yes"):
        return False
    settings = get_settings()
    return not settings.lazy_rag_init


def create_app(*, load_rag_on_startup: bool = True) -> FastAPI:
    configure_logging()
    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info(
            "Starting MediAssist API (environment=%s, lazy_rag=%s)",
            settings.environment,
            settings.lazy_rag_init,
        )
        try:
            await run_in_threadpool(init_db)
            logger.info("Database tables ready")
        except Exception:
            logger.exception("Database init failed — check DATABASE_URL and PostgreSQL.")
            raise
        if _should_eager_load_rag(load_rag_on_startup=load_rag_on_startup):
            try:
                await run_in_threadpool(init_rag_chain)
            except Exception:
                logger.exception(
                    "RAG init failed at startup (symptoms mode unavailable until lazy load)."
                )
            try:
                await run_in_threadpool(init_mental_health_chain)
            except Exception:
                logger.exception(
                    "Mental health RAG init failed — direct Groq mental health mode still works."
                )
            try:
                await run_in_threadpool(init_lab_results_chain)
            except Exception:
                logger.exception(
                    "Lab results RAG init failed — parser + reference JSON lab mode still works."
                )
        yield
        logger.info("Shutting down MediAssist API")

    application = FastAPI(
        title="MediAssist API",
        description="MediAssist medical assistant API (educational use only).",
        version="1.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        RateLimitMiddleware,
        limiter=InMemoryRateLimiter(settings.rate_limit_per_minute),
    )

    _cors_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in _cors_origins if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(mock_router)
    application.include_router(appointments_router)
    application.include_router(attachments_router)
    application.mount(
        "/static",
        StaticFiles(directory=str(BASE_DIR / "static")),
        name="static",
    )

    @application.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(status="ok", rag_ready=is_rag_ready())

    @application.post("/api/chat", response_model=ChatResponse)
    async def chat_api(body: ChatRequest):
        message = body.msg.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        try:
            if not await run_in_threadpool(ensure_rag_chain):
                raise HTTPException(
                    status_code=503,
                    detail="Symptom knowledge base is not available.",
                )
            answer = await run_in_threadpool(invoke_rag, message)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("RAG invocation failed")
            raise HTTPException(
                status_code=503,
                detail="Unable to generate a response. Please try again later.",
            ) from exc
        if not answer:
            raise HTTPException(
                status_code=503,
                detail="Empty response from the model.",
            )
        logger.info("Chat response generated (%d chars)", len(answer))
        return ChatResponse(answer=answer)

    @application.post("/get", response_model=ChatResponse)
    async def chat_form(msg: str = Form(..., min_length=1, max_length=2000)):
        return await chat_api(ChatRequest(msg=msg))

    if not register_production_frontend(application, BASE_DIR):

        @application.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            return templates.TemplateResponse(request=request, name="chat.html", context={})

    return application
