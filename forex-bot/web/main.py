"""
Forex Analiz Bot — Web Panel (FastAPI)

Ishga tushirish:
    uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload

Bot bilan birga ishga tushirish uchun run.py dan foydalaning.
"""
import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import BOT_TOKEN, DATABASE_URL
from database.db import close_pool, create_pool, init_db
from web.routers import (
    analysis,
    broadcast,
    channels,
    dashboard,
    premium,
    settings,
    signals,
    users,
)


# ─── LIFESPAN ────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    pool = await create_pool(DATABASE_URL)
    await init_db(pool)
    app.state.pool = pool

    # Bot ni ham bog'laymiz (agar bot.py dan state uzatilsa)
    # Standalone rejimda bot None bo'ladi
    app.state.bot = getattr(app.state, "bot", None)

    yield

    # Shutdown
    await close_pool(pool)


# ─── APP ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Forex Analiz Bot — Web Panel",
    version="1.0.0",
    docs_url="/api/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ROUTERS ─────────────────────────────────────────────────────

app.include_router(settings.router)
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(signals.router)
app.include_router(channels.router)
app.include_router(premium.router)
app.include_router(broadcast.router)
app.include_router(analysis.router)

# ─── STATIC FILES ────────────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str = ""):
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"detail": "index.html topilmadi"}
