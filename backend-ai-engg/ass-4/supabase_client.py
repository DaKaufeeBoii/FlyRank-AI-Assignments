"""Supabase Client initialization and configuration for Assignment 4."""

import logging
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from supabase import Client, create_client

logger = logging.getLogger("auth_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Explicitly load .env from the current package directory or parent workspace
ENV_PATH = Path(__file__).resolve().parent / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://your-project-id.supabase.co")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "your_supabase_anon_key_here")
PORT: int = int(os.getenv("PORT", "8000"))

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return the shared Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be configured in environment or .env"
            )
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


def init_supabase() -> Client:
    """Verify and initialize Supabase connection on startup."""
    client = get_supabase_client()
    logger.info("Server running and connected to Supabase")
    return client
