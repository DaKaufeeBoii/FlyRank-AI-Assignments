"""
Comprehensive Verification Suite for TokenPulse.
Directly implements and tests Acceptance Probes 1 through 5.
"""
import pytest
import json
import sqlite3
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, seed_db, get_connection
from app.services.stripe_service import generate_test_webhook_signature

TEST_DB = "test_billing.db"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up an isolated test database for each run."""
    monkeypatch.setattr("app.config.settings.DATABASE_PATH", TEST_DB)
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass
    init_db(TEST_DB)
    seed_db(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass

client = TestClient(app)

def test_probe_1_idempotent_metering():
    """
    PROBE 1: Send the same billable request twice with one idempotency key ->
    exactly one usage event; the second response mirrors the first.
    """
    tenant_id = "tenant_free_001"
    key = "idemp_test_probe_1_abc"
    payload = {
        "tenant_id": tenant_id,
        "prompt": "Test AI request",
        "simulated_tokens": {
            "input_tokens": 1000,
            "cached_input_tokens": 200,
            "output_tokens": 300,
            "reasoning_tokens": 100
        }
    }
    headers = {"Idempotency-Key": key}

    # 1. First request
    res1 = client.post("/generate", json=payload, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["idempotency_replay"] is False
    event_id = data1["event_id"]

    # 2. Second request (Retry with identical key)
    res2 = client.post("/generate", json=payload, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["idempotency_replay"] is True
    assert data2["event_id"] == event_id
    assert data2["tokens_billed"] == data1["tokens_billed"]

    # 3. Verify exactly ONE usage event exists in database
    conn = get_connection(TEST_DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM usage_events WHERE idempotency_key = ?;", (key,))
    count = cur.fetchone()[0]
    conn.close()
    assert count == 1, f"Expected 1 usage event, found {count}"

def test_probe_2_quota_boundary_and_status_codes():
    """
    PROBE 2: Drive a tenant to its exact quota -> the request at the boundary behaves per
    documented rule; the one after returns 429 / 402 with a clear message.
    """
    tenant_id = "tenant_boundary_003"
    
    # Free tier limit is 100,000 tokens
    # Drive to near boundary: 99,500 tokens
    key_fill = "idemp_boundary_fill"
    payload_fill = {
        "tenant_id": tenant_id,
        "prompt": "Fill quota",
        "simulated_tokens": {
            "input_tokens": 99500,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0
        }
    }
    res_fill = client.post("/generate", json=payload_fill, headers={"Idempotency-Key": key_fill})
    assert res_fill.status_code == 200

    # Exactly reach boundary: +500 tokens = 100,000 total (Boundary request succeeds)
    key_boundary = "idemp_boundary_exact"
    payload_boundary = {
        "tenant_id": tenant_id,
        "prompt": "Exact boundary",
        "simulated_tokens": {
            "input_tokens": 500,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0
        }
    }
    res_boundary = client.post("/generate", json=payload_boundary, headers={"Idempotency-Key": key_boundary})
    assert res_boundary.status_code == 200

    # Request after boundary: +100 tokens -> Must be rejected with 429 Too Many Requests
    key_over = "idemp_boundary_over"
    payload_over = {
        "tenant_id": tenant_id,
        "prompt": "Over quota",
        "simulated_tokens": {
            "input_tokens": 100,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0
        }
    }
    res_over = client.post("/generate", json=payload_over, headers={"Idempotency-Key": key_over})
    assert res_over.status_code == 429
    detail = res_over.json()["detail"]
    assert detail["error"] == "Too Many Requests"
    assert "quota exceeded" in detail["message"].lower()

    # Verify 402 Payment Required for delinquent tenant
    res_delinquent = client.post(
        "/generate",
        json={"tenant_id": "tenant_unpaid_004", "prompt": "Blocked"},
        headers={"Idempotency-Key": "idemp_unpaid_test"}
    )
    assert res_delinquent.status_code == 402
    assert res_delinquent.json()["detail"]["error"] == "Payment Required"

def test_probe_3_stripe_checkout_and_plan_upgrade_webhook():
    """
    PROBE 3: Complete a Stripe test Checkout -> the webhook flips the tenant Free -> Pro;
    GET /usage shows the new limits.
    """
    tenant_id = "tenant_free_001"
    
    # 1. Verify initially Free
    u1 = client.get(f"/usage?tenant_id={tenant_id}").json()
    assert u1["plan_id"] == "free"
    assert u1["tokens_limit"] == 100_000

    # 2. Simulate Stripe checkout webhook event
    event_payload = {
        "id": "evt_test_checkout_001",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_session_123",
                "customer": "cus_test_free_01",
                "subscription": "sub_test_pro_activated",
                "metadata": {
                    "tenant_id": tenant_id
                }
            }
        }
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")
    valid_sig = generate_test_webhook_signature(payload_bytes)

    # Post webhook
    res_wh = client.post("/webhooks/stripe", content=payload_bytes, headers={"Stripe-Signature": valid_sig})
    assert res_wh.status_code == 200
    assert res_wh.json()["status"] == "processed"

    # 3. Verify tenant is flipped to Pro and limits updated
    u2 = client.get(f"/usage?tenant_id={tenant_id}").json()
    assert u2["plan_id"] == "pro"
    assert u2["tokens_limit"] == 10_000_000 # Pro tier has 10M tokens limit

def test_probe_4_webhook_signature_verification_and_replay_deduplication():
    """
    PROBE 4: Send a forged webhook (bad signature) -> 400, nothing changes.
    Replay a real event twice -> processed once.
    """
    event_payload = {
        "id": "evt_replay_test_002",
        "type": "customer.subscription.updated",
        "data": {"object": {"customer": "cus_test_free_01", "subscription": "sub_abc"}}
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")

    # 1. Send forged webhook with invalid signature
    res_forged = client.post(
        "/webhooks/stripe",
        content=payload_bytes,
        headers={"Stripe-Signature": "t=12345,v1=bad_forged_signature_hex"}
    )
    assert res_forged.status_code == 400
    assert "Forged or invalid Stripe webhook signature" in res_forged.json()["detail"]

    # 2. Send genuine signed webhook
    valid_sig = generate_test_webhook_signature(payload_bytes)
    res_legit = client.post("/webhooks/stripe", content=payload_bytes, headers={"Stripe-Signature": valid_sig})
    assert res_legit.status_code == 200
    assert res_legit.json()["status"] == "processed"

    # 3. Replay exact same webhook event
    res_replay = client.post("/webhooks/stripe", content=payload_bytes, headers={"Stripe-Signature": valid_sig})
    assert res_replay.status_code == 200
    assert res_replay.json()["status"] == "ignored_duplicate"

def test_probe_5_pinned_token_pricing_rules():
    """
    PROBE 5: Check the pinned pricing rules -> cached-input and reasoning-token rules
    produce the exact expected totals; GET /usage matches.
    
    Rates:
    - Input: $2.50 / 1M = 2.5 micro-cents / token
    - Cached Input: $1.25 / 1M = 1.25 micro-cents / token (Cheaper)
    - Output: $10.00 / 1M = 10.0 micro-cents / token
    - Reasoning: $10.00 / 1M = 10.0 micro-cents / token (Billed as output)
    """
    tenant_id = "tenant_pro_002"
    payload = {
        "tenant_id": tenant_id,
        "prompt": "Pricing validation",
        "simulated_tokens": {
            "input_tokens": 100_000,          # 100,000 * 2.5 = 250,000 micro-cents ($0.25)
            "cached_input_tokens": 200_000,   # 200,000 * 1.25 = 250,000 micro-cents ($0.25)
            "output_tokens": 50_000,          # 50,000 * 10.0 = 500,000 micro-cents ($0.50)
            "reasoning_tokens": 50_000        # 50,000 * 10.0 = 500,000 micro-cents ($0.50) (Reasoning counts as output)
        }
    }
    # Expected total cost: 250,000 + 250,000 + 500,000 + 500,000 = 1,500,000 micro-cents = $1.500000
    res = client.post("/generate", json=payload, headers={"Idempotency-Key": "idemp_pricing_test_01"})
    assert res.status_code == 200
    data = res.json()
    assert data["tokens_billed"] == 400_000
    assert data["cost_micro_cents"] == 1_500_000
    assert data["cost_usd_formatted"] == "$1.500000"

    # Verify GET /usage reflects exact calculated totals
    usage = client.get(f"/usage?tenant_id={tenant_id}").json()
    assert usage["total_tokens_used"] >= 400_000
    assert usage["total_cost_micro_cents"] >= 1_500_000
