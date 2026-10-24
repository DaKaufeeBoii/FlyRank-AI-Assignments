"""FastAPI Authentication API with Supabase Auth."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
import uvicorn

from supabase_client import PORT, init_supabase

logger = logging.getLogger("auth_api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan context: initialize Supabase client on startup."""
    init_supabase()
    yield


app = FastAPI(
    title="Secure Auth API",
    version="1.0.0",
    description="FastAPI service with Supabase Auth, JWT verification, and protected routes.",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify server is active."""
    return {"status": "ok", "service": "Supabase Auth API"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
