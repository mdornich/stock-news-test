"""
Data gathering modules for news, SEC filings, and market data
"""

import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yfinance as yf
from config import (
    NEWSAPI_KEY,
    FINNHUB_API_KEY,
    ALPHA_VANTAGE_API_KEY,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    STOCKTWITS_API_KEY,
    NEWS_LOOKBACK_HOURS,
    REDDIT_LOOKBACK_HOURS,
    get_lookback_date,
    get_sec_lookback_date,
    calculate_recency_weight,
)


class NewsArticle:
    """Represents a news article with recency weighting and source tracking"""

    def __init__(
        self,
        title: str,
        description: str,
        url: str,
        published_at: datetime,
        source: str,
        data_source_type: str,
        sentiment: Optional[float] = None,
    ):
        self.title = title
        self.description = description
        self.url = url
        self.published_at = published_at
        self.source = source  # Original publisher (e.g., "Reuters", "Bloomberg")
        self.data_source_type = data_source_type  # API used (e.g., "NewsAPI", "Finnhub")
        self.sentiment = sentiment  # Optional sentiment score (-1 to 1)
        self.weight, self.recency_label = calculate_recency_weight(published_at)

    def __repr__(self):
        return f"<NewsArticle: {self.title[:50]}... (source={self.data_source_type}, weight={self.weight}, {self.recency_label})>"

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "source": self.source,
            "data_source_type": self.data_source_type,
            "sentiment": self.sentiment,
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
                    data_source_type="NewsAPI",
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

# ============================================================================
# Additional Data Source Gatherers
# ============================================================================


def fetch_finnhub_news(symbol: str) -> List[NewsArticle]:
    """
    Fetch news from Finnhub API (real-time, sub-minute latency)
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        List of NewsArticle objects from Finnhub
    """
    if not FINNHUB_API_KEY:
        print("Info: FINNHUB_API_KEY not found, skipping Finnhub")
        return []
    
    lookback_date = get_lookback_date()
    from_date = lookback_date.strftime("%Y-%m-%d")
    to_date = datetime.utcnow().strftime("%Y-%m-%d")
    
    url = f"https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": symbol,
        "from": from_date,
        "to": to_date,
        "token": FINNHUB_API_KEY,
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for item in data:
            try:
                published_at = datetime.fromtimestamp(item.get("datetime", 0))
                
                # Finnhub provides sentiment score
                sentiment = item.get("sentiment", None)
                
                news_article = NewsArticle(
                    title=item.get("headline", ""),
                    description=item.get("summary", ""),
                    url=item.get("url", ""),
                    published_at=published_at,
                    source=item.get("source", "Finnhub"),
                    data_source_type="Finnhub",
                    sentiment=sentiment,
                )
                articles.append(news_article)
            except Exception as e:
                print(f"Warning: Error parsing Finnhub article: {e}")
                continue
        
        return articles
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Finnhub news: {e}")
        return []


def fetch_alpha_vantage_news(symbol: str) -> List[NewsArticle]:
    """
    Fetch news sentiment from Alpha Vantage
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        List of NewsArticle objects from Alpha Vantage
    """
    if not ALPHA_VANTAGE_API_KEY:
        print("Info: ALPHA_VANTAGE_API_KEY not found, skipping Alpha Vantage")
        return []
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "limit": 200,
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for item in data.get("feed", []):
            try:
                # Parse time published (format: 20231115T120000)
                time_str = item.get("time_published", "")
                published_at = datetime.strptime(time_str, "%Y%m%dT%H%M%S")
                
                # Check if within our lookback window
                if published_at < get_lookback_date():
                    continue
                
                # Extract ticker-specific sentiment
                ticker_sentiment = None
                for ticker_data in item.get("ticker_sentiment", []):
                    if ticker_data.get("ticker") == symbol:
                        ticker_sentiment = float(ticker_data.get("ticker_sentiment_score", 0))
                        break
                
                news_article = NewsArticle(
                    title=item.get("title", ""),
                    description=item.get("summary", "")[:500],  # Truncate if too long
                    url=item.get("url", ""),
                    published_at=published_at,
                    source=item.get("source", "Alpha Vantage"),
                    data_source_type="AlphaVantage",
                    sentiment=ticker_sentiment,
                )
                articles.append(news_article)
            except Exception as e:
                print(f"Warning: Error parsing Alpha Vantage article: {e}")
                continue
        
        return articles
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Alpha Vantage news: {e}")
        return []


def fetch_google_news(symbol: str, company_name: str) -> List[NewsArticle]:
    """
    Fetch news from Google News RSS feed (free, no API key needed)
    
    Args:
        symbol: Stock ticker symbol
        company_name: Company name for search
    
    Returns:
        List of NewsArticle objects from Google News
    """
    # Google News RSS feed URL
    query = f"{company_name} stock {symbol}"
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(url)
        
        articles = []
        for entry in feed.entries:
            try:
                # Parse published date
                published_at = datetime(*entry.published_parsed[:6])
                
                # Check if within our lookback window
                if published_at < get_lookback_date():
                    continue
                
                news_article = NewsArticle(
                    title=entry.title,
                    description=entry.get("summary", ""),
                    url=entry.link,
                    published_at=published_at,
                    source=entry.get("source", {}).get("title", "Google News"),
                    data_source_type="GoogleNews",
                )
                articles.append(news_article)
            except Exception as e:
                print(f"Warning: Error parsing Google News article: {e}")
                continue
        
        return articles
    
    except Exception as e:
        print(f"Error fetching Google News: {e}")
        return []


def fetch_reddit_posts(symbol: str, company_name: str) -> List[NewsArticle]:
    """
    Fetch relevant posts from Reddit (r/wallstreetbets, r/stocks)
    
    Args:
        symbol: Stock ticker symbol
        company_name: Company name
    
    Returns:
        List of NewsArticle objects from Reddit
    """
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("Info: Reddit credentials not found, skipping Reddit")
        return []
    
    try:
        # Get Reddit OAuth token
        auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
        data = {"grant_type": "client_credentials"}
        headers = {"User-Agent": REDDIT_USER_AGENT}
        
        token_response = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data=data,
            headers=headers,
            timeout=10,
        )
        token_response.raise_for_status()
        token = token_response.json().get("access_token")
        
        headers["Authorization"] = f"bearer {token}"
        
        # Search multiple subreddits
        subreddits = ["wallstreetbets", "stocks", "investing"]
        articles = []
        
        for subreddit in subreddits:
            # Search for symbol and company name
            search_url = f"https://oauth.reddit.com/r/{subreddit}/search"
            params = {
                "q": f"{symbol} OR {company_name}",
                "sort": "new",
                "limit": 25,
                "restrict_sr": True,
                "t": "day",  # Last 24 hours
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for post in data.get("data", {}).get("children", []):
                try:
                    post_data = post.get("data", {})
                    
                    # Convert Unix timestamp to datetime
                    published_at = datetime.fromtimestamp(post_data.get("created_utc", 0))
                    
                    # Check if within lookback window
                    lookback = datetime.utcnow() - timedelta(hours=REDDIT_LOOKBACK_HOURS)
                    if published_at < lookback:
                        continue
                    
                    # Create article from Reddit post
                    title = post_data.get("title", "")
                    selftext = post_data.get("selftext", "")
                    url = f"https://reddit.com{post_data.get('permalink', '')}"
                    
                    # Use upvote ratio as a proxy for sentiment
                    upvote_ratio = post_data.get("upvote_ratio", 0.5)
                    sentiment = (upvote_ratio - 0.5) * 2  # Convert to -1 to 1 scale
                    
                    news_article = NewsArticle(
                        title=f"[r/{subreddit}] {title}",
                        description=selftext[:500] if selftext else title,
                        url=url,
                        published_at=published_at,
                        source=f"Reddit r/{subreddit}",
                        data_source_type="Reddit",
                        sentiment=sentiment,
                    )
                    articles.append(news_article)
                except Exception as e:
                    print(f"Warning: Error parsing Reddit post: {e}")
                    continue
        
        return articles
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Reddit posts: {e}")
        return []


def fetch_stocktwits(symbol: str) -> List[NewsArticle]:
    """
    Fetch messages from StockTwits (financial social network)
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        List of NewsArticle objects from StockTwits
    """
    # Note: StockTwits API v2 doesn't require API key for basic access
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for message in data.get("messages", []):
            try:
                # Parse created_at timestamp
                created_str = message.get("created_at", "")
                published_at = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%SZ")
                
                # Check if within lookback window
                if published_at < get_lookback_date():
                    continue
                
                # Extract sentiment from entities
                sentiment_data = message.get("entities", {}).get("sentiment", {})
                sentiment_basic = sentiment_data.get("basic", "")
                
                # Convert to numeric sentiment
                sentiment = None
                if sentiment_basic == "Bullish":
                    sentiment = 0.5
                elif sentiment_basic == "Bearish":
                    sentiment = -0.5
                
                # Get message body
                body = message.get("body", "")
                
                news_article = NewsArticle(
                    title=f"[StockTwits] {body[:100]}",
                    description=body[:500],
                    url=f"https://stocktwits.com/{message.get('user', {}).get('username', '')}/message/{message.get('id', '')}",
                    published_at=published_at,
                    source="StockTwits",
                    data_source_type="StockTwits",
                    sentiment=sentiment,
                )
                articles.append(news_article)
            except Exception as e:
                print(f"Warning: Error parsing StockTwits message: {e}")
                continue
        
        return articles
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching StockTwits: {e}")
        return []


def fetch_insider_trades(symbol: str) -> List[Dict]:
    """
    Enhanced SEC Form 4 insider trading detection
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        List of insider trading events
    """
    headers = {
        "User-Agent": "Stock Explainer Bot contact@example.com"
    }
    
    try:
        # Get company CIK
        ticker_url = "https://www.sec.gov/files/company_tickers.json"
        ticker_response = requests.get(ticker_url, headers=headers, timeout=10)
        ticker_response.raise_for_status()
        ticker_data = ticker_response.json()
        
        cik = None
        for item in ticker_data.values():
            if item.get("ticker", "").upper() == symbol.upper():
                cik = str(item.get("cik_str", "")).zfill(10)
                break
        
        if not cik:
            return []
        
        # Fetch submissions
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        sub_response = requests.get(submissions_url, headers=headers, timeout=10)
        sub_response.raise_for_status()
        submissions = sub_response.json()
        
        recent_filings = submissions.get("filings", {}).get("recent", {})
        if not recent_filings:
            return []
        
        # Extract Form 4 filings (insider trades)
        lookback_date = get_sec_lookback_date()
        insider_trades = []
        
        filing_dates = recent_filings.get("filingDate", [])
        filing_types = recent_filings.get("form", [])
        
        for i in range(min(len(filing_dates), 50)):
            try:
                filing_date = datetime.strptime(filing_dates[i], "%Y-%m-%d")
                filing_type = filing_types[i]
                
                if filing_date >= lookback_date and filing_type == "4":
                    insider_trades.append({
                        "type": "Insider Trading (Form 4)",
                        "date": filing_dates[i],
                        "description": "Insider buy/sell transaction",
                        "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=4&dateb=&owner=include&count=10",
                    })
            except Exception as e:
                continue
        
        return insider_trades
    
    except Exception as e:
        print(f"Error fetching insider trades: {e}")
        return []


def fetch_earnings_and_options(symbol: str) -> Dict:
    """
    Fetch earnings calendar and unusual options activity from Yahoo Finance
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Dictionary with earnings and options data
    """
    try:
        stock = yf.Ticker(symbol)
        
        # Get earnings calendar
        earnings_data = stock.calendar
        options_data = {}
        
        # Get options chain
        try:
            options_dates = stock.options
            if options_dates:
                # Get nearest expiration
                nearest_expiry = options_dates[0]
                opt_chain = stock.option_chain(nearest_expiry)
                
                # Calculate put/call ratio
                total_call_volume = opt_chain.calls['volume'].sum()
                total_put_volume = opt_chain.puts['volume'].sum()
                
                put_call_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else 0
                
                options_data = {
                    "nearest_expiry": nearest_expiry,
                    "put_call_ratio": round(put_call_ratio, 2),
                    "total_call_volume": int(total_call_volume),
                    "total_put_volume": int(total_put_volume),
                }
        except Exception as e:
            print(f"Warning: Could not fetch options data: {e}")
        
        return {
            "earnings": earnings_data,
            "options": options_data,
        }
    
    except Exception as e:
        print(f"Error fetching earnings/options: {e}")
        return {"earnings": None, "options": {}}


def aggregate_all_news(symbol: str, company_name: str) -> List[NewsArticle]:
    """
    Aggregate news from all available sources
    
    Args:
        symbol: Stock ticker symbol
        company_name: Company name
    
    Returns:
        Combined and deduplicated list of NewsArticle objects from all sources
    """
    all_articles = []
    
    print("   └─ Fetching from NewsAPI...")
    all_articles.extend(fetch_news(symbol, company_name))
    
    print("   └─ Fetching from Finnhub...")
    all_articles.extend(fetch_finnhub_news(symbol))
    
    print("   └─ Fetching from Alpha Vantage...")
    all_articles.extend(fetch_alpha_vantage_news(symbol))
    
    print("   └─ Fetching from Google News...")
    all_articles.extend(fetch_google_news(symbol, company_name))
    
    print("   └─ Fetching from Reddit...")
    all_articles.extend(fetch_reddit_posts(symbol, company_name))
    
    print("   └─ Fetching from StockTwits...")
    all_articles.extend(fetch_stocktwits(symbol))
    
    # Deduplicate by URL and title similarity
    unique_articles = []
    seen_urls = set()
    seen_titles = set()
    
    for article in all_articles:
        # Skip if we've seen this URL
        if article.url and article.url in seen_urls:
            continue
        
        # Skip if we've seen very similar title
        title_lower = article.title.lower()[:100]
        if title_lower in seen_titles:
            continue
        
        seen_urls.add(article.url)
        seen_titles.add(title_lower)
        unique_articles.append(article)
    
    # Sort by weight (highest first), then by published date
    unique_articles.sort(key=lambda x: (x.weight, x.published_at), reverse=True)
    
    print(f"   └─ Total articles collected: {len(unique_articles)} (after deduplication)")
    
    return unique_articles
