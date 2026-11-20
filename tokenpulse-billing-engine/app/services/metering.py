"""
Usage Metering Service with strict Idempotency Guarantees.
Prevents double-counting by deduplicating requests via Idempotency-Key.
"""
import json
import uuid
import hashlib
import sqlite3
from typing import Tuple, Dict, Any
from app.database import transaction
from app.models import GenerateRequest, GenerateResponse, TokenBreakdown
from app.services.pricing import calculate_token_cost_micro_cents, format_micro_cents_to_usd
from app.services.quota import check_tenant_quota

def process_billable_generation(
    conn: sqlite3.Connection,
    request: GenerateRequest,
    idempotency_key: str
) -> Tuple[int, Dict[str, Any]]:
    """
    Executes a billable generation action idempotently.
    
    1. Checks if idempotency_key was already processed for this tenant.
       -> If YES, return the exact stored response (no double charge, no duplicate event).
    2. Runs quota enforcement check.
    3. Calculates exact token costs using integer micro-cents.
    4. Records usage event and persists idempotency cache atomically.
    """
    cur = conn.cursor()
    
    # 1. Probe for duplicate idempotency key
    cur.execute("""
    SELECT response_code, response_body 
    FROM idempotency_records 
    WHERE key = ? AND tenant_id = ?;
    """, (idempotency_key, request.tenant_id))
    existing = cur.fetchone()
    
    if existing:
        # Return exact cached result, zero duplicate charge
        cached_body = json.loads(existing["response_body"])
        cached_body["idempotency_replay"] = True
        return existing["response_code"], cached_body

    # Calculate requested token breakdown
    tokens = request.simulated_tokens or TokenBreakdown()
    total_tokens, cost_micro_cents = calculate_token_cost_micro_cents(tokens)
    
    # 2. Check Quotas before recording
    tenant = check_tenant_quota(conn, request.tenant_id, total_tokens)
    
    # 3. Store usage event and idempotency record inside an atomic transaction
    with transaction(conn) as cur_tx:
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        cur_tx.execute("""
        INSERT INTO usage_events (
            id, tenant_id, idempotency_key, action_type, api_calls_count,
            input_tokens, cached_input_tokens, output_tokens, reasoning_tokens,
            cost_micro_cents
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            event_id,
            request.tenant_id,
            idempotency_key,
            "generate_ai_completion",
            1,
            tokens.input_tokens,
            tokens.cached_input_tokens,
            tokens.output_tokens,
            tokens.reasoning_tokens,
            cost_micro_cents
        ))
        
        response_data = {
            "status": "success",
            "event_id": event_id,
            "tenant_id": request.tenant_id,
            "idempotency_key": idempotency_key,
            "tokens_billed": total_tokens,
            "token_breakdown": tokens.model_dump(),
            "cost_micro_cents": cost_micro_cents,
            "cost_usd_formatted": format_micro_cents_to_usd(cost_micro_cents),
            "idempotency_replay": False,
            "message": "Usage successfully metered and billed."
        }
        
        req_hash = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
        cur_tx.execute("""
        INSERT INTO idempotency_records (key, tenant_id, endpoint, request_hash, response_code, response_body)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (
            idempotency_key,
            request.tenant_id,
            "/generate",
            req_hash,
            200,
            json.dumps(response_data)
        ))
        
    return 200, response_data
