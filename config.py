"""
Configuration and constants for stock explainer
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys - Core
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# API Keys - News Sources
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# API Keys - Social Media
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "StockExplainerBot/1.0")
STOCKTWITS_API_KEY = os.getenv("STOCKTWITS_API_KEY")

# API Keys - Twitter/X (optional, for scraping)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")  # If available

# Stock Configuration
DEFAULT_SYMBOL = "NVDA"
DEFAULT_COMPANY_NAME = "NVIDIA"

# Time Windows
NEWS_LOOKBACK_HOURS = 48
SEC_LOOKBACK_DAYS = 7  # Check for SEC filings in past week
REDDIT_LOOKBACK_HOURS = 24  # Reddit posts/comments
TWITTER_LOOKBACK_HOURS = 12  # Twitter is very fast-moving

# Data Source Metadata
# Track which sources are free vs paid, and their characteristics
DATA_SOURCES = {
    "NewsAPI": {"cost": "free", "tier": "freemium", "limit": "100/day", "latency": "minutes"},
    "Finnhub": {"cost": "free", "tier": "freemium", "limit": "60/min", "latency": "seconds"},
    "AlphaVantage": {"cost": "free", "tier": "freemium", "limit": "5/min", "latency": "minutes"},
    "GoogleNews": {"cost": "free", "tier": "free", "limit": "unlimited", "latency": "minutes"},
    "Reddit": {"cost": "free", "tier": "free", "limit": "60/min", "latency": "real-time"},
    "StockTwits": {"cost": "free", "tier": "freemium", "limit": "200/hour", "latency": "real-time"},
    "SEC-Edgar": {"cost": "free", "tier": "free", "limit": "10/sec", "latency": "minutes-hours"},
    "YahooFinance": {"cost": "free", "tier": "free", "limit": "2000/hour", "latency": "minutes"},
    "Twitter": {"cost": "paid", "tier": "paid", "limit": "varies", "latency": "real-time"},
}

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
