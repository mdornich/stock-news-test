"""
Configuration and constants for stock explainer
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Stock Configuration
DEFAULT_SYMBOL = "NVDA"
DEFAULT_COMPANY_NAME = "NVIDIA"

# Time Windows
NEWS_LOOKBACK_HOURS = 48
SEC_LOOKBACK_DAYS = 7  # Check for SEC filings in past week

# Recency Weighting Configuration
# News articles are weighted based on how recent they are
WEIGHT_TIERS = [
    {"max_hours": 12, "weight": 1.0, "label": "Very Recent"},
    {"max_hours": 24, "weight": 0.7, "label": "Recent"},
    {"max_hours": 36, "weight": 0.4, "label": "Moderately Recent"},
    {"max_hours": 48, "weight": 0.2, "label": "Older"},
]


def calculate_recency_weight(published_at: datetime) -> tuple[float, str]:
    """
    Calculate the recency weight for a news article based on when it was published.

    Args:
        published_at: datetime when the article was published

    Returns:
        tuple of (weight, label) where weight is between 0.0-1.0
    """
    now = datetime.utcnow()
    hours_ago = (now - published_at).total_seconds() / 3600

    for tier in WEIGHT_TIERS:
        if hours_ago <= tier["max_hours"]:
            return tier["weight"], tier["label"]

    # Default for anything older than our tiers
    return 0.1, "Very Old"


def get_lookback_date():
    """Get the date to look back to for news (48 hours ago)"""
    return datetime.utcnow() - timedelta(hours=NEWS_LOOKBACK_HOURS)


def get_sec_lookback_date():
    """Get the date to look back to for SEC filings"""
    return datetime.utcnow() - timedelta(days=SEC_LOOKBACK_DAYS)
