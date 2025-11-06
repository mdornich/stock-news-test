"""
Data gathering modules for news, SEC filings, and market data
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
import yfinance as yf
from config import (
    NEWSAPI_KEY,
    NEWS_LOOKBACK_HOURS,
    get_lookback_date,
    get_sec_lookback_date,
    calculate_recency_weight,
)


class NewsArticle:
    """Represents a news article with recency weighting"""

    def __init__(self, title: str, description: str, url: str, published_at: datetime, source: str):
        self.title = title
        self.description = description
        self.url = url
        self.published_at = published_at
        self.source = source
        self.weight, self.recency_label = calculate_recency_weight(published_at)

    def __repr__(self):
        return f"<NewsArticle: {self.title[:50]}... (weight={self.weight}, {self.recency_label})>"

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "source": self.source,
            "weight": self.weight,
            "recency_label": self.recency_label,
        }


def fetch_news(symbol: str, company_name: str) -> List[NewsArticle]:
    """
    Fetch news articles about the stock from NewsAPI

    Args:
        symbol: Stock ticker symbol (e.g., 'NVDA')
        company_name: Company name for search (e.g., 'NVIDIA')

    Returns:
        List of NewsArticle objects, sorted by recency weight (highest first)
    """
    if not NEWSAPI_KEY:
        print("Warning: NEWSAPI_KEY not found in environment variables")
        return []

    lookback_date = get_lookback_date()
    from_date = lookback_date.strftime("%Y-%m-%d")

    # Search for company name and stock symbol
    query = f'("{company_name}" OR "${symbol}") AND (stock OR shares OR trading OR earnings OR revenue)'

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWSAPI_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get("articles", []):
            try:
                # Parse the published date
                published_str = article.get("publishedAt", "")
                published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))

                news_article = NewsArticle(
                    title=article.get("title", ""),
                    description=article.get("description", ""),
                    url=article.get("url", ""),
                    published_at=published_at.replace(tzinfo=None),  # Remove timezone for simplicity
                    source=article.get("source", {}).get("name", "Unknown"),
                )
                articles.append(news_article)
            except Exception as e:
                print(f"Warning: Error parsing article: {e}")
                continue

        # Sort by weight (highest first), then by published date
        articles.sort(key=lambda x: (x.weight, x.published_at), reverse=True)

        return articles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []


def fetch_sec_filings(symbol: str) -> List[Dict]:
    """
    Fetch recent SEC filings for the stock

    Args:
        symbol: Stock ticker symbol (e.g., 'NVDA')

    Returns:
        List of recent SEC filings with type, date, and description
    """
    # SEC EDGAR API endpoint
    headers = {
        "User-Agent": "Stock Explainer Bot contact@example.com"  # SEC requires a user agent
    }

    try:
        # Get company CIK (Central Index Key) first
        cik_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker={symbol}&output=json"
        response = requests.get(cik_url, headers=headers, timeout=10)

        # SEC might return HTML even with json output parameter, so we need to handle this carefully
        # For now, we'll use a simpler approach with the submissions endpoint

        # Alternative: Use the company submissions endpoint
        # First, we need to get the CIK. Let's try the company tickers JSON
        ticker_url = "https://www.sec.gov/files/company_tickers.json"
        ticker_response = requests.get(ticker_url, headers=headers, timeout=10)
        ticker_response.raise_for_status()
        ticker_data = ticker_response.json()

        # Find the CIK for our symbol
        cik = None
        for item in ticker_data.values():
            if item.get("ticker", "").upper() == symbol.upper():
                cik = str(item.get("cik_str", "")).zfill(10)  # Pad CIK to 10 digits
                break

        if not cik:
            print(f"Warning: Could not find CIK for symbol {symbol}")
            return []

        # Fetch recent submissions
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        sub_response = requests.get(submissions_url, headers=headers, timeout=10)
        sub_response.raise_for_status()
        submissions = sub_response.json()

        # Extract recent filings
        recent_filings = submissions.get("filings", {}).get("recent", {})

        if not recent_filings:
            return []

        # Get filings from the lookback period
        lookback_date = get_sec_lookback_date()
        filings = []

        filing_dates = recent_filings.get("filingDate", [])
        filing_types = recent_filings.get("form", [])
        accession_numbers = recent_filings.get("accessionNumber", [])
        primary_docs = recent_filings.get("primaryDocument", [])

        for i in range(min(len(filing_dates), 20)):  # Check up to 20 most recent
            try:
                filing_date = datetime.strptime(filing_dates[i], "%Y-%m-%d")

                if filing_date >= lookback_date:
                    filing_type = filing_types[i]
                    accession = accession_numbers[i].replace("-", "")

                    filing = {
                        "type": filing_type,
                        "date": filing_dates[i],
                        "description": get_filing_description(filing_type),
                        "url": f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}/{primary_docs[i]}",
                    }
                    filings.append(filing)
            except Exception as e:
                print(f"Warning: Error parsing filing: {e}")
                continue

        return filings

    except requests.exceptions.RequestException as e:
        print(f"Error fetching SEC filings: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching SEC filings: {e}")
        return []


def get_filing_description(filing_type: str) -> str:
    """Get a human-readable description of the SEC filing type"""
    descriptions = {
        "8-K": "Current Report (Material Events)",
        "10-K": "Annual Report",
        "10-Q": "Quarterly Report",
        "4": "Insider Trading Report",
        "S-1": "Registration Statement",
        "S-3": "Registration Statement",
        "424B5": "Prospectus Filing",
        "DEF 14A": "Proxy Statement",
    }
    return descriptions.get(filing_type, filing_type)


def fetch_market_data(symbol: str) -> Optional[Dict]:
    """
    Fetch basic market data for the stock using yfinance

    Args:
        symbol: Stock ticker symbol (e.g., 'NVDA')

    Returns:
        Dictionary with price, volume, market cap, sector info, etc.
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="5d")

        if hist.empty:
            print(f"Warning: No historical data found for {symbol}")
            return None

        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest

        market_data = {
            "symbol": symbol,
            "current_price": round(latest["Close"], 2),
            "previous_close": round(prev["Close"], 2),
            "price_change": round(latest["Close"] - prev["Close"], 2),
            "price_change_pct": round(((latest["Close"] - prev["Close"]) / prev["Close"]) * 100, 2),
            "volume": int(latest["Volume"]),
            "avg_volume": int(hist["Volume"].mean()),
            "volume_ratio": round(latest["Volume"] / hist["Volume"].mean(), 2),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("marketCap", "Unknown"),
            "company_name": info.get("longName", "Unknown"),
        }

        return market_data

    except Exception as e:
        print(f"Error fetching market data: {e}")
        return None
