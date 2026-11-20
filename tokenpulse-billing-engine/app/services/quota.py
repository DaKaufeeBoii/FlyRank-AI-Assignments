"""
Quota enforcement service.
Checks limits before allowing billable actions.
Emits clear RFC-compliant 429 Too Many Requests or 402 Payment Required.
"""
import sqlite3
from fastapi import HTTPException
from app.config import settings

def check_tenant_quota(conn: sqlite3.Connection, tenant_id: str, requested_tokens: int) -> dict:
    """
    Checks if a tenant is allowed to execute a billable request.
    Raises HTTPException(402) if subscription is delinquent.
    Raises HTTPException(429) if quota boundary is exceeded.
    Returns tenant record dict on success.
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM tenants WHERE id = ?;", (tenant_id,))
    tenant = cur.fetchone()
    
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found.")
    
    plan_id = tenant["plan_id"]
    sub_status = tenant["subscription_status"]
    
    # Check 1: 402 Payment Required if subscription has failed or is delinquent
    if sub_status in ("past_due", "unpaid", "canceled"):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Payment Required",
                "message": f"Tenant subscription status is '{sub_status}'. Please update payment method to resume access.",
                "tenant_id": tenant_id,
                "status_code": 402
            }
        )
    
    plan_config = settings.PLAN_QUOTAS.get(plan_id, settings.PLAN_QUOTAS["free"])
    api_limit = plan_config["api_calls_limit"]
    token_limit = plan_config["tokens_limit"]
    
    # Query current usage for this tenant
    cur.execute("""
    SELECT 
        COALESCE(SUM(api_calls_count), 0) as current_calls,
        COALESCE(SUM(input_tokens + cached_input_tokens + output_tokens + reasoning_tokens), 0) as current_tokens
    FROM usage_events
    WHERE tenant_id = ?;
    """, (tenant_id,))
    usage = cur.fetchone()
    current_calls = usage["current_calls"]
    current_tokens = usage["current_tokens"]
    
    # Check 2: 429 Too Many Requests on API calls quota boundary
    if current_calls + 1 > api_limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too Many Requests",
                "message": f"Monthly API call quota exceeded. Used {current_calls} of {api_limit} allowed calls. Upgrade plan for higher limits.",
                "limit_type": "api_calls",
                "current_usage": current_calls,
                "limit": api_limit,
                "retry_after": 3600
            },
            headers={"Retry-After": "3600"}
        )
        
    # Check 3: 429 Too Many Requests on Token quota boundary
    if current_tokens + requested_tokens > token_limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too Many Requests",
                "message": f"Monthly token quota exceeded. Current {current_tokens} + requested {requested_tokens} > limit {token_limit}. Upgrade to Pro for 10M tokens.",
                "limit_type": "tokens",
                "current_usage": current_tokens,
                "requested": requested_tokens,
                "limit": token_limit,
                "retry_after": 3600
            },
            headers={"Retry-After": "3600"}
        )
        
    return dict(tenant)
