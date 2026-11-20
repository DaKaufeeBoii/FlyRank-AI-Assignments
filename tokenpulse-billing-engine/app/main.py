"""
TokenPulse — LLM Usage Metering & Billing Engine.
FastAPI Application Entry Point.
"""
from fastapi import FastAPI, Request, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import get_connection, init_db, seed_db
from app.models import (
    GenerateRequest,
    GenerateResponse,
    UsageRollupResponse,
    CheckoutRequest,
    CheckoutResponse
)
from app.services.metering import process_billable_generation
from app.services.pricing import format_micro_cents_to_usd
from app.services.stripe_service import (
    verify_stripe_webhook_signature,
    process_stripe_webhook_event
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema and seed default data
    init_db()
    seed_db()
    yield

app = FastAPI(
    title="TokenPulse — LLM Usage Metering & Billing Engine",
    description="Deterministic usage metering, quota enforcement, exact AI token pricing math, and Stripe test-mode subscription synchronization.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["System"])
def root():
    return {
        "service": "TokenPulse Metering & Billing Engine",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["System"])
def health():
    # Verify database connection
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        db_ok = cur.fetchone()[0] == 1
    finally:
        conn.close()
    return {"status": "healthy", "database": "connected" if db_ok else "error"}

@app.get("/plans", tags=["Billing"])
def get_plans():
    """Returns available subscription tiers and their monthly quotas."""
    return settings.PLAN_QUOTAS

@app.post("/generate", response_model=GenerateResponse, tags=["Metering"])
async def billable_generate(
    request: GenerateRequest,
    idempotency_key: str = Header(None, alias="Idempotency-Key")
):
    """
    Billable AI Generation Endpoint.
    Requires an Idempotency-Key header.
    - Exactly-once metering: Retrying with the same key returns the original result with 0 duplicate charge.
    - Quota check: Blocks with 429 when monthly allowance is reached; blocks with 402 if subscription is unpaid.
    - Token math: Accurately prices input, cheaper cached input, output, and reasoning tokens.
    """
    if not idempotency_key or len(idempotency_key.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Header 'Idempotency-Key' is required for all billable generation requests."
        )

    conn = get_connection()
    try:
        code, response_data = process_billable_generation(conn, request, idempotency_key.strip())
        return response_data
    finally:
        conn.close()

@app.get("/usage", response_model=UsageRollupResponse, tags=["Usage"])
def get_usage(tenant_id: str = Query(..., description="Tenant ID to inspect usage for")):
    """
    Returns monthly usage rollup for a tenant:
    - Total API calls vs limit
    - Total tokens consumed vs limit
    - Calculated total cost in USD (derived from integer micro-cents)
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tenants WHERE id = ?;", (tenant_id,))
        tenant = cur.fetchone()
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found.")
            
        plan_id = tenant["plan_id"]
        plan_cfg = settings.PLAN_QUOTAS.get(plan_id, settings.PLAN_QUOTAS["free"])
        
        cur.execute("""
        SELECT 
            COALESCE(SUM(api_calls_count), 0) as total_calls,
            COALESCE(SUM(input_tokens + cached_input_tokens + output_tokens + reasoning_tokens), 0) as total_tokens,
            COALESCE(SUM(cost_micro_cents), 0) as total_cost_micro_cents
        FROM usage_events
        WHERE tenant_id = ?;
        """, (tenant_id,))
        stats = cur.fetchone()
        
        total_calls = stats["total_calls"]
        total_tokens = stats["total_tokens"]
        total_cost = stats["total_cost_micro_cents"]
        
        api_limit = plan_cfg["api_calls_limit"]
        token_limit = plan_cfg["tokens_limit"]
        
        return UsageRollupResponse(
            tenant_id=tenant["id"],
            tenant_name=tenant["name"],
            plan_id=plan_id,
            subscription_status=tenant["subscription_status"],
            total_api_calls=total_calls,
            api_calls_limit=api_limit,
            api_calls_remaining=max(0, api_limit - total_calls),
            total_tokens_used=total_tokens,
            tokens_limit=token_limit,
            tokens_remaining=max(0, token_limit - total_tokens),
            total_cost_micro_cents=total_cost,
            total_cost_usd_formatted=format_micro_cents_to_usd(total_cost),
            quota_reached=(total_calls >= api_limit or total_tokens >= token_limit)
        )
    finally:
        conn.close()

@app.post("/checkout", response_model=CheckoutResponse, tags=["Stripe"])
def create_checkout_session(req: CheckoutRequest):
    """
    Simulates / initiates a Stripe Checkout session to upgrade a tenant to Pro.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tenants WHERE id = ?;", (req.tenant_id,))
        tenant = cur.fetchone()
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant '{req.tenant_id}' not found.")
            
        session_id = f"cs_test_{req.tenant_id[:8]}_upgrade_pro"
        checkout_url = f"https://checkout.stripe.com/pay/{session_id}"
        
        return CheckoutResponse(
            checkout_url=checkout_url,
            session_id=session_id,
            tenant_id=req.tenant_id,
            plan=req.target_plan
        )
    finally:
        conn.close()

@app.post("/webhooks/stripe", tags=["Stripe"])
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """
    Stripe Webhook Listener.
    - Cryptographically verifies signature (rejects forged with 400).
    - Deduplicates events (replayed event ID ignored).
    - Updates tenant plan/status on checkout.session.completed (Free -> Pro).
    """
    payload_bytes = await request.body()
    
    if not verify_stripe_webhook_signature(payload_bytes, stripe_signature):
        raise HTTPException(
            status_code=400,
            detail="Forged or invalid Stripe webhook signature. Request rejected."
        )
        
    try:
        event = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON in webhook payload")
        
    conn = get_connection()
    try:
        code, result = process_stripe_webhook_event(conn, event)
        return result
    finally:
        conn.close()

@app.post("/seed", tags=["System"])
def trigger_seed():
    """Resets database and loads baseline demo data."""
    init_db()
    seed_db()
    return {"status": "success", "message": "Database reseeded with test tenants and plans."}
