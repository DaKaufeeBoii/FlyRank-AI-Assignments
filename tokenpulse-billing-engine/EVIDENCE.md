# TokenPulse Billing Engine — Evidence Document (EVIDENCE.md)
**Author:** Sai Tarun Reddy (`saitarunrdy@gmail.com`)  
**Track:** Backend AI Engineering Capstone  
**Target:** Usage Metering & Billing Engine  

This document contains verifiable outputs and execution proof for all contract requirements in Section 6 and acceptance probes in Section 12.

---

## 1. Automated Acceptance Probes Test Run

```bash
$ python -m pytest tests/test_probes.py -v
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Kaufee\padhai\Internships\FlyRank.ai\tokenpulse-billing-engine
plugins: anyio-4.15.0, asyncio-1.4.0, cov-7.1.0, mock-3.15.1
collected 5 items

tests/test_probes.py::test_probe_1_idempotent_metering PASSED            [ 20%]
tests/test_probes.py::test_probe_2_quota_boundary_and_status_codes PASSED [ 40%]
tests/test_probes.py::test_probe_3_stripe_checkout_and_plan_upgrade_webhook PASSED [ 60%]
tests/test_probes.py::test_probe_4_webhook_signature_verification_and_replay_deduplication PASSED [ 80%]
tests/test_probes.py::test_probe_5_pinned_token_pricing_rules PASSED     [100%]

======================== 5 passed in 1.15s ========================
```

---

## 2. Requirement Proofs (Section 6 Contract)

### [x] Metering: Exactly-once metering under retries
* **Proof:** Verified in `test_probe_1_idempotent_metering`.
* **Execution Evidence:**
```json
// Request 1: POST /generate (Idempotency-Key: idemp_test_probe_1_abc)
HTTP/1.1 200 OK
{
  "status": "success",
  "event_id": "evt_49a17fd20c91",
  "tenant_id": "tenant_free_001",
  "idempotency_key": "idemp_test_probe_1_abc",
  "tokens_billed": 1600,
  "cost_micro_cents": 6750,
  "cost_usd_formatted": "$0.006750",
  "idempotency_replay": false,
  "message": "Usage successfully metered and billed."
}

// Request 2 (Retry with identical key): POST /generate
HTTP/1.1 200 OK
{
  "status": "success",
  "event_id": "evt_49a17fd20c91",
  "tenant_id": "tenant_free_001",
  "idempotency_key": "idemp_test_probe_1_abc",
  "tokens_billed": 1600,
  "cost_micro_cents": 6750,
  "cost_usd_formatted": "$0.006750",
  "idempotency_replay": true,
  "message": "Usage successfully metered and billed."
}
```
* **Database Verification:** `SELECT COUNT(*) FROM usage_events WHERE idempotency_key = 'idemp_test_probe_1_abc'` returns `1`. No duplicate billing event is recorded.

---

### [x] Quota Enforcement: Boundary honesty & HTTP status codes
* **Proof:** Verified in `test_probe_2_quota_boundary_and_status_codes`.
* **Execution Evidence:**
  - Tenant driven to exact 100,000 token limit returns `200 OK`.
  - Next request exceeding boundary is rejected:
```json
HTTP/1.1 429 Too Many Requests
Retry-After: 3600
{
  "detail": {
    "error": "Too Many Requests",
    "message": "Monthly token quota exceeded. Current 100000 + requested 100 > limit 100000. Upgrade to Pro for 10M tokens.",
    "limit_type": "tokens",
    "current_usage": 100000,
    "requested": 100,
    "limit": 100000,
    "retry_after": 3600
  }
}
```
  - Unpaid / delinquent tenant is blocked with `402 Payment Required`:
```json
HTTP/1.1 402 Payment Required
{
  "detail": {
    "error": "Payment Required",
    "message": "Tenant subscription status is 'past_due'. Please update payment method to resume access.",
    "tenant_id": "tenant_unpaid_004",
    "status_code": 402
  }
}
```

---

### [x] Cost Calculation: Real-world AI token rules (cached, reasoning, integers)
* **Proof:** Verified in `test_probe_5_pinned_token_pricing_rules`.
* **Execution Evidence:**
  - Token Breakdown:
    - Fresh Input: 100,000 tokens × 2.5 micro-cents = 250,000 micro-cents ($0.25)
    - Cached Input: 200,000 tokens × 1.25 micro-cents = 250,000 micro-cents ($0.25) *(Cheaper)*
    - Standard Output: 50,000 tokens × 10.0 micro-cents = 500,000 micro-cents ($0.50)
    - Reasoning Tokens: 50,000 tokens × 10.0 micro-cents = 500,000 micro-cents ($0.50) *(Counts as output)*
  - Sum: `250,000 + 250,000 + 500,000 + 500,000 = 1,500,000 micro-cents = $1.500000`
```json
HTTP/1.1 200 OK
{
  "status": "success",
  "tokens_billed": 400000,
  "cost_micro_cents": 1500000,
  "cost_usd_formatted": "$1.500000"
}
```

---

### [x] Stripe Webhook: Signature verification & replay deduplication
* **Proof:** Verified in `test_probe_3` and `test_probe_4`.
* **Execution Evidence:**
  - Forged webhook with invalid signature returns `400 Bad Request`:
```json
HTTP/1.1 400 Bad Request
{
  "detail": "Forged or invalid Stripe webhook signature. Request rejected."
}
```
  - Legit signed webhook flips tenant from `free` to `pro`:
```json
HTTP/1.1 200 OK
{
  "status": "processed",
  "event_id": "evt_test_checkout_001",
  "event_type": "checkout.session.completed",
  "message": "Tenant subscription successfully updated via verified webhook."
}
```
  - Replaying identical event returns `200 OK` with duplicate ignored flag:
```json
HTTP/1.1 200 OK
{
  "status": "ignored_duplicate",
  "message": "Webhook event 'evt_replay_test_002' was already processed. Skipped without duplicate actions."
}
```
