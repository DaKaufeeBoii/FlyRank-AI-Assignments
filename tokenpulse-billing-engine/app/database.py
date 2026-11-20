"""
Database management with SQLite in WAL mode and ACID transaction boundaries.
"""
import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config import settings

def get_connection(db_path: str = None) -> sqlite3.Connection:
    path = db_path or settings.DATABASE_PATH
    conn = sqlite3.connect(path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Cursor, None, None]:
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE;")
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise

def init_db(db_path: str = None) -> None:
    conn = get_connection(db_path)
    with transaction(conn) as cur:
        # 1. Tenants table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            plan_id TEXT NOT NULL DEFAULT 'free',
            subscription_status TEXT NOT NULL DEFAULT 'active',
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # 2. Idempotency records table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS idempotency_records (
            key TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            request_hash TEXT NOT NULL,
            response_code INTEGER NOT NULL,
            response_body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        );
        """)

        # 3. Usage events table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usage_events (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            idempotency_key TEXT UNIQUE NOT NULL,
            action_type TEXT NOT NULL,
            api_calls_count INTEGER NOT NULL DEFAULT 1,
            input_tokens INTEGER NOT NULL DEFAULT 0,
            cached_input_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            reasoning_tokens INTEGER NOT NULL DEFAULT 0,
            cost_micro_cents INTEGER NOT NULL DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        );
        """)

        # 4. Webhook idempotency table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Create Indexes for fast querying & boundary checks
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_tenant ON usage_events(tenant_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage_events(timestamp);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_tenant ON idempotency_records(tenant_id);")
    conn.close()

def seed_db(db_path: str = None) -> None:
    conn = get_connection(db_path)
    with transaction(conn) as cur:
        # Seed default test tenants
        tenants = [
            ("tenant_free_001", "Acme Corp (Free)", "free@acme.com", "free", "active", "cus_test_free_01", None),
            ("tenant_pro_002", "Globex Inc (Pro)", "pro@globex.com", "pro", "active", "cus_test_pro_02", "sub_test_pro_02"),
            ("tenant_boundary_003", "EdgeCase Labs", "edge@test.com", "free", "active", "cus_test_edge_03", None),
            ("tenant_unpaid_004", "Delinquent Co", "unpaid@test.com", "pro", "past_due", "cus_test_unpaid_04", "sub_test_unpaid_04")
        ]
        for t in tenants:
            cur.execute("""
            INSERT OR REPLACE INTO tenants (id, name, email, plan_id, subscription_status, stripe_customer_id, stripe_subscription_id)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, t)
    conn.close()
