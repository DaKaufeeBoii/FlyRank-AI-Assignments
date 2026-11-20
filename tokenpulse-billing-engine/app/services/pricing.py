"""
Pricing calculation service enforcing exact AI token pricing rules.
All calculations use integer micro-cents (1 USD = 1,000,000 micro-cents).
Never floats.
"""
from typing import Tuple
from app.config import settings
from app.models import TokenBreakdown

def calculate_token_cost_micro_cents(tokens: TokenBreakdown) -> Tuple[int, int]:
    """
    Calculates the exact cost of an AI generation event in integer micro-cents.
    
    Rules:
    - Input tokens: $2.50 / 1M tokens (250 scaled micro-cents)
    - Cached input tokens: $1.25 / 1M tokens (125 scaled micro-cents) -> CHEAPER
    - Output tokens: $10.00 / 1M tokens (1000 scaled micro-cents)
    - Reasoning tokens: $10.00 / 1M tokens (1000 scaled micro-cents) -> COUNTS AS OUTPUT
    
    Returns:
        (total_tokens_count, total_cost_micro_cents)
    """
    p = settings.PRICING_MICRO_CENTS_PER_TOKEN
    scale = settings.SCALE_FACTOR
    
    # Integer scaled math: (tokens * rate) // scale
    cost_input = (tokens.input_tokens * p["input"]) // scale
    cost_cached = (tokens.cached_input_tokens * p["cached_input"]) // scale
    cost_output = (tokens.output_tokens * p["output"]) // scale
    cost_reasoning = (tokens.reasoning_tokens * p["reasoning"]) // scale
    
    total_cost_micro_cents = cost_input + cost_cached + cost_output + cost_reasoning
    total_tokens = (
        tokens.input_tokens + 
        tokens.cached_input_tokens + 
        tokens.output_tokens + 
        tokens.reasoning_tokens
    )
    
    return total_tokens, total_cost_micro_cents

def format_micro_cents_to_usd(micro_cents: int) -> str:
    """Formats micro-cents to standard USD string: e.g. 1,250,000 -> '$1.250000'"""
    dollars = micro_cents // 1_000_000
    cents_remainder = (micro_cents % 1_000_000)
    return f"${dollars}.{cents_remainder:06d}"
