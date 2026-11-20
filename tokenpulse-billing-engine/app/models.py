"""
Pydantic Data Schemas and Validation Models.
"""
from typing import Optional, List
from pydantic import BaseModel, Field

class TokenBreakdown(BaseModel):
    input_tokens: int = Field(ge=0, default=500, description="Fresh input tokens")
    cached_input_tokens: int = Field(ge=0, default=0, description="Cheaper cached input tokens")
    output_tokens: int = Field(ge=0, default=200, description="Standard generated output tokens")
    reasoning_tokens: int = Field(ge=0, default=0, description="Thinking tokens (billed as output)")

class GenerateRequest(BaseModel):
    tenant_id: str = Field(min_length=1, description="Tenant ID to attribute usage to")
    prompt: str = Field(default="Generate summary of document", min_length=1)
    simulated_tokens: Optional[TokenBreakdown] = Field(default_factory=TokenBreakdown)

class GenerateResponse(BaseModel):
    status: str
    event_id: Optional[str] = None
    tenant_id: str
    idempotency_key: str
    tokens_billed: int
    cost_micro_cents: int
    cost_usd_formatted: str
    idempotency_replay: bool = False
    message: str

class UsageRollupResponse(BaseModel):
    tenant_id: str
    tenant_name: str
    plan_id: str
    subscription_status: str
    total_api_calls: int
    api_calls_limit: int
    api_calls_remaining: int
    total_tokens_used: int
    tokens_limit: int
    tokens_remaining: int
    total_cost_micro_cents: int
    total_cost_usd_formatted: str
    quota_reached: bool

class CheckoutRequest(BaseModel):
    tenant_id: str
    target_plan: str = "pro"
    success_url: str = "https://example.com/billing/success"
    cancel_url: str = "https://example.com/billing/cancel"

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
    tenant_id: str
    plan: str
