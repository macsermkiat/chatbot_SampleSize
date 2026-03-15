from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.billing import router as billing_router
from app.api.chat import router as chat_router
from app.api.files import router as files_router
from app.api.sessions import router as sessions_router
from app.config import settings, validate_required_keys
from app.db import check_db, close_pool, get_pool
from app.models import HealthResponse
from app.services.memory import close_checkpointer, open_checkpointer


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging
    logger = logging.getLogger(__name__)

    # Validate API keys at startup
    for warning in validate_required_keys():
        logger.warning(warning)

    # Startup: warm the connection pool (graceful if DB unavailable)
    if settings.has_database:
        try:
            pool = await get_pool()
            await _run_migrations(pool)
        except Exception as exc:
            logger.warning("DB pool/migration failed, starting in degraded mode: %s", exc)
    else:
        logger.info("No DATABASE_URL configured -- running without PostgreSQL")

    # Always initialise the checkpointer (falls back to in-memory if no DB)
    checkpointer = await open_checkpointer()
    app.state.checkpointer = checkpointer

    yield

    # Shutdown
    try:
        await close_checkpointer()
        await close_pool()
    except Exception:
        pass


async def _run_migrations(pool) -> None:
    """Execute SQL migration files from backend/migrations/ in order."""
    import pathlib

    migrations_dir = pathlib.Path(__file__).resolve().parent.parent / "migrations"
    if not migrations_dir.is_dir():
        return

    async with pool.acquire() as conn:
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            await conn.execute(sql_file.read_text())


app = FastAPI(
    title="Medical Research Assistant",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(billing_router)
app.include_router(chat_router)
app.include_router(files_router)
app.include_router(sessions_router)


@app.get("/ping")
async def ping():
    """Lightweight liveness check -- no DB, no I/O."""
    return {"status": "ok"}


@app.get("/health", response_model=HealthResponse)
async def health():
    db_ok = await check_db()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db=db_ok,
    )
