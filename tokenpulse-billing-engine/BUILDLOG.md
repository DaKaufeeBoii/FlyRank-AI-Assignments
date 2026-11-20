# TokenPulse Billing Engine — Build Log (BUILDLOG.md)
**Author:** Sai Tarun Reddy (`saitarunrdy@gmail.com`)  
**Track:** Backend AI Engineering Capstone  

This log provides an honest, transparent record of how AI assistance was leveraged, where it proposed flawed patterns, and the architectural corrections I enforced.

---

## 1. Where AI Assistance Helped
- **FastAPI Endpoint Scaffolding:** Accelerated boilerplates for request typing, header extraction (`Idempotency-Key`), and dependency injection.
- **HMAC-SHA256 Webhook Verification:** Accurately generated the string concatenation template (`{timestamp}.{payload}`) conforming to Stripe's raw webhook verification specifications.
- **Pytest Fixture Structure:** Provided clean test isolation patterns using monkeypatching for database paths.

---

## 2. Where AI Was Wrong & Required Correction

### Issue 1: Floating-Point Rounding in Currency Calculations
* **The AI's Proposal:**  
  The initial AI draft used Python `float` variables (`cost = round(tokens * 0.0000025, 4)`).
* **Why It Was Rejected:**  
  In financial billing systems, floating-point arithmetic produces non-deterministic precision drift (e.g. `0.1 + 0.2 = 0.30000000000000004`).
* **My Correction:**  
  I strictly refactored the pricing engine to use **integer micro-cents** (where 1 USD = 1,000,000 micro-cents). Every operation uses integer multiplication and division with a fixed scale factor, completely eliminating precision errors.

### Issue 2: Silent Exception Swallowing in Idempotency Lookup
* **The AI's Proposal:**  
  AI suggested wrapping duplicate checking in a generic try-catch block that logged a warning and continued.
* **Why It Was Rejected:**  
  If an idempotency lookup fails due to a database deadlock or query issue, allowing the request to proceed would double-charge the customer.
* **My Correction:**  
  I made idempotency lookups strict and transactional: if an existing key is found, the stored result is returned immediately with `idempotency_replay: true`. If a database error occurs, the request aborts with 500 rather than risking a duplicate write.

### Issue 3: Pydantic Response Serialization Filtering
* **The AI's Proposal:**  
  AI missed including `idempotency_replay` and `event_id` in the `GenerateResponse` schema.
* **My Correction:**  
  FastAPI stripped those fields during serialization, causing probe test assertion failures. I explicitly updated the Pydantic schema to include both fields with typed defaults.

---

## 3. Defense Verification
I can explain every line of this codebase:
- The exact SQLite WAL mode configuration and `BEGIN IMMEDIATE` transaction locking.
- The HMAC-SHA256 constant-time comparison (`hmac.compare_digest`) preventing timing attacks.
- The 429 vs 402 status code semantics and boundary evaluation.
