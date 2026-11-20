"""
Configuration and Pinned Pricing Constants.
All money math strictly uses integer micro-cents (1 USD = 100 cents = 1,000,000 micro-cents).
Never floats.
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_PATH: str = "billing.db"
    
    # Stripe Test Configuration
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "sk_test_dummy_key")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret_32bytes_minimum_length_hash")
    STRIPE_PRO_PRICE_ID: str = os.getenv("STRIPE_PRO_PRICE_ID", "price_pro_plan_test")

    # Plan Quotas (monthly limits)
    PLAN_QUOTAS: dict = {
        "free": {
            "name": "Free Tier",
            "api_calls_limit": 1000,
            "tokens_limit": 100_000,
            "cost_cents": 0
        },
        "pro": {
            "name": "Pro Tier",
            "api_calls_limit": 50_000,
            "tokens_limit": 10_000_000,
            "cost_cents": 4900 # $49.00/month
        }
    }

    # Pinned Token Pricing Rules (per 1,000,000 tokens)
    # Stored in micro-cents: 1 USD = 1,000,000 micro-cents
    # - Standard Input: $2.50 / 1M tokens = 2,500,000 micro-cents per 1M tokens (= 2.5 micro-cents / token)
    # - Cached Input: $1.25 / 1M tokens = 1,250,000 micro-cents per 1M tokens (= 1.25 micro-cents / token) (Cheaper)
    # - Standard Output: $10.00 / 1M tokens = 10,000,000 micro-cents per 1M tokens (= 10.0 micro-cents / token)
    # - Reasoning Tokens: Count as Output tokens ($10.00 / 1M tokens = 10,000,000 micro-cents per 1M tokens)
    PRICING_MICRO_CENTS_PER_TOKEN: dict = {
        "input": 250,           # 2.5 micro-cents per token * 100 (scaled for integer math)
        "cached_input": 125,    # 1.25 micro-cents per token * 100
        "output": 1000,         # 10.0 micro-cents per token * 100
        "reasoning": 1000       # 10.0 micro-cents per token * 100 (reasoning counts as output)
    }
    SCALE_FACTOR: int = 100     # divisor to normalize scaled micro-cents to micro-cents

settings = Settings()
