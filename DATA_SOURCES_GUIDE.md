# Data Sources Setup Guide

This guide explains all 9 data sources integrated into the Stock Catalyst Analyzer, how to set them up, and what value each provides.

## Quick Reference Table

| Source | Cost | Credentials Needed | Access Method | Timeliness | Setup Time |
|--------|------|-------------------|---------------|------------|------------|
| NewsAPI | Free/Paid | ✅ Yes | API | Minutes | 2 min |
| Finnhub | Free/Paid | ✅ Yes | API | Seconds | 2 min |
| Alpha Vantage | Free/Paid | ✅ Yes | API | Minutes | 2 min |
| Google News | Free | ❌ No | RSS Feed | Minutes | 0 min |
| Reddit | Free | ✅ Yes | OAuth API | Real-time | 5 min |
| StockTwits | Free | ❌ No | Public API | Real-time | 0 min |
| SEC EDGAR | Free | ❌ No | Public API | Hours | 0 min |
| Yahoo Finance | Free | ❌ No | yfinance Library | Minutes | 0 min |
| Twitter/X | Paid | ✅ Yes | API (v2) | Real-time | N/A |

---

## 1. NewsAPI

### Overview
- **Website**: https://newsapi.org/
- **Cost**: Free tier available (100 requests/day)
- **Latency**: ~5-15 minutes
- **Value**: Broad news aggregation from 80,000+ sources

### Setup Instructions
1. Go to https://newsapi.org/
2. Click "Get API Key"
3. Sign up with email
4. Copy your API key
5. Add to `.env`:
   ```
   NEWSAPI_KEY=your_key_here
   ```

### Free Tier Limits
- 100 requests per day
- 1-month historical data
- News from 80,000+ sources

### Paid Tier Benefits ($449/month)
- Unlimited requests
- 2-year historical data
- Commercial use allowed

### What We Do With It
- Fetch all news articles mentioning the stock ticker or company name
- Filter for financial keywords (stock, shares, trading, earnings)
- Past 48 hours of coverage

---

## 2. Finnhub

### Overview
- **Website**: https://finnhub.io/
- **Cost**: Free tier available (60 API calls/min)
- **Latency**: Sub-minute (very fast!)
- **Value**: Real-time financial news with sentiment scores

### Setup Instructions
1. Go to https://finnhub.io/register
2. Sign up for free account
3. Navigate to Dashboard → API Keys
4. Copy your API key
5. Add to `.env`:
   ```
   FINNHUB_API_KEY=your_key_here
   ```

### Free Tier Limits
- 60 API calls per minute
- Company news, sentiment, financials

### Paid Tier Benefits ($59-$399/month)
- Higher rate limits
- Real-time data feeds
- Advanced analytics

### What We Do With It
- Fetch company-specific news with timestamps
- Extract sentiment scores (if available)
- Very timely data - often beats NewsAPI

**Recommendation**: ⭐ **High priority** - Free tier is generous and data is very timely

---

## 3. Alpha Vantage

### Overview
- **Website**: https://www.alphavantage.co/
- **Cost**: Free tier available (5 API calls/min)
- **Latency**: ~10-30 minutes
- **Value**: News sentiment analysis with ticker-specific scores

### Setup Instructions
1. Go to https://www.alphavantage.co/support/#api-key
2. Enter your email
3. API key sent instantly to email
4. Add to `.env`:
   ```
   ALPHA_VANTAGE_API_KEY=your_key_here
   ```

### Free Tier Limits
- 5 API calls per minute
- 500 calls per day
- News & sentiment API included

### Paid Tier Benefits ($49.99-$249.99/month)
- Higher rate limits
- Real-time data
- Premium support

### What We Do With It
- Fetch news with sentiment scores
- Get ticker-specific sentiment (not just article-level)
- Identify sentiment shifts

---

## 4. Google News

### Overview
- **Website**: N/A (uses RSS feeds)
- **Cost**: Completely free
- **Latency**: ~5-20 minutes
- **Value**: Quick news aggregation, no API key needed

### Setup Instructions
**NO SETUP REQUIRED** - works out of the box!

### How It Works
- We parse Google News RSS feeds
- Search for stock ticker + company name
- No authentication needed
- Uses the `feedparser` library

### What We Do With It
- Fetch recent news articles
- Aggregate from various sources via Google News
- Fallback option if paid APIs are down

**Recommendation**: ⭐ **Always use** - It's free and requires zero setup

---

## 5. Reddit

### Overview
- **Website**: https://www.reddit.com/prefs/apps
- **Cost**: Free
- **Latency**: Real-time
- **Value**: Retail investor sentiment from r/wallstreetbets, r/stocks, r/investing

### Setup Instructions
1. Log into Reddit account (create one if needed)
2. Go to https://www.reddit.com/prefs/apps
3. Scroll to bottom, click "Create App" or "Create Another App"
4. Fill out the form:
   - **Name**: Stock Explainer Bot
   - **App type**: Select "script"
   - **Description**: Personal stock analysis tool
   - **About URL**: (leave blank)
   - **Redirect URI**: http://localhost:8080
5. Click "Create app"
6. Copy the credentials:
   - **Client ID**: The string under "personal use script"
   - **Client Secret**: The "secret" field
7. Add to `.env`:
   ```
   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_client_secret_here
   REDDIT_USER_AGENT=StockExplainerBot/1.0 by YourRedditUsername
   ```

### Rate Limits
- 60 API calls per minute
- OAuth2 authentication required

### What We Do With It
- Search r/wallstreetbets, r/stocks, r/investing
- Find posts mentioning the ticker or company
- Use upvote ratio as sentiment proxy
- Detect "meme stock" catalysts early

**Recommendation**: ⭐ **Highly recommended** - Catches retail-driven moves that news misses

---

## 6. StockTwits

### Overview
- **Website**: https://stocktwits.com/
- **Cost**: Free (no API key needed for basic access)
- **Latency**: Real-time
- **Value**: Financial social network with built-in sentiment

### Setup Instructions
**NO SETUP REQUIRED** - uses public API!

### How It Works
- StockTwits API v2 is publicly accessible
- No authentication needed for basic stream access
- Returns messages with Bullish/Bearish sentiment

### What We Do With It
- Fetch recent messages for the stock ticker
- Extract Bullish/Bearish sentiment
- Identify unusual chatter volume

**Recommendation**: ⭐ **Always use** - Free, no setup, real-time sentiment

---

## 7. SEC EDGAR

### Overview
- **Website**: https://www.sec.gov/edgar
- **Cost**: Free
- **Latency**: Hours (filings appear within hours of submission)
- **Value**: Official company filings (8-K, 10-K, 10-Q, Form 4)

### Setup Instructions
**NO SETUP REQUIRED** - public API!

### Important Note
- SEC requires a User-Agent header with contact info
- We use: `Stock Explainer Bot contact@example.com`
- You may want to update this in `gatherers.py` to your email

### What We Do With It
- Check for material events (8-K filings)
- Detect insider trading (Form 4)
- Find quarterly/annual reports (10-Q/10-K)
- Past 7 days of filings

**Recommendation**: ⭐ **Always use** - Free, authoritative, no setup

---

## 8. Yahoo Finance

### Overview
- **Website**: https://finance.yahoo.com/
- **Cost**: Free
- **Latency**: ~5-15 minutes for market data
- **Value**: Market data, earnings calendar, options chain

### Setup Instructions
**NO SETUP REQUIRED** - uses yfinance library!

### How It Works
- `yfinance` library provides unofficial access to Yahoo Finance
- No API key needed
- Can break if Yahoo changes their website

### What We Do With It
- Fetch current price, volume, market cap
- Get earnings calendar
- Calculate put/call ratio from options chain
- Determine if unusual volume

**Recommendation**: ⭐ **Always use** - Free, reliable, covers the basics

---

## 9. Twitter/X

### Overview
- **Website**: https://developer.twitter.com/
- **Cost**: Paid only (Basic $100/month, Pro $5,000/month)
- **Latency**: Real-time
- **Value**: Breaking news from key financial accounts

### Setup Instructions
**Currently implemented but NOT RECOMMENDED unless you already have API access**

Elon's pricing changed Twitter API to paid-only. If you have API access:

1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a project and app
3. Generate Bearer Token
4. Add to `.env`:
   ```
   TWITTER_BEARER_TOKEN=your_bearer_token_here
   ```

### What We Would Do With It
- Monitor key accounts: @DeItaone, @Fxhedgers, @unusual_whales
- Catch breaking news seconds before mainstream media
- Track verified insider accounts

### Current Status
- **NOT IMPLEMENTED in current code** (no function written yet)
- Placeholder in config only
- Can add if user has API access

**Recommendation**: ❌ **Skip** unless you already have Twitter API access

---

## Setup Priority Recommendation

Based on value vs. effort, here's the recommended setup order:

### Tier 1: Do These First (High Value, Easy Setup)
1. ✅ **Anthropic API** - Required for analysis
2. ✅ **Google News** - No setup needed
3. ✅ **StockTwits** - No setup needed
4. ✅ **SEC EDGAR** - No setup needed
5. ✅ **Yahoo Finance** - No setup needed

### Tier 2: Do These Next (High Value, 2-5 min setup)
6. ⭐ **Finnhub** - 2 min signup, very timely data
7. ⭐ **NewsAPI** - 2 min signup, broad coverage
8. ⭐ **Reddit** - 5 min setup, retail sentiment

### Tier 3: Optional (Nice to Have)
9. 💡 **Alpha Vantage** - Sentiment scores, but rate-limited
10. ❌ **Twitter/X** - Skip unless you have paid API

---

## After Setup: How to Test

1. Copy `.env.example` to `.env`
2. Add your API keys
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`
5. Check the **DATA SOURCE VALUE REPORT** in the output
6. It will show which sources provided data and their value scores

---

## Cost-Benefit Analysis

After running the tool a few times, check the source value report:

```
Source Performance (ranked by value):
Source                Articles    Avg Weight   High-Value   Cost        Latency
------------------------------------------------------------------------------------
★ Finnhub             15          0.850        12 (80%)     free        seconds
★ Reddit              8           0.725        6 (75%)      free        real-time
★ NewsAPI             20          0.650        10 (50%)     free        minutes
  AlphaVantage        5           0.400        1 (20%)      free        minutes
  GoogleNews          12          0.550        4 (33%)      free        minutes
```

### Decision Guide
- **High avg weight + high article count** → Valuable source, keep using
- **Free tier source with ★** → Definitely keep
- **Freemium source with ★** → Consider upgrading to paid tier
- **Low avg weight + few articles** → Maybe skip this source

---

## Troubleshooting

### "Info: [SOURCE] not found, skipping"
- This is normal - just means you haven't set up that API key yet
- The tool gracefully skips sources without credentials

### Rate Limit Errors
- **Alpha Vantage**: Wait 1 minute (5 calls/min limit)
- **NewsAPI**: You've hit daily limit (100/day on free tier)
- **Reddit**: Wait 1 minute (60 calls/min)

### No Data from a Source
- Check your API key is correct in `.env`
- Verify the API key is active in the provider's dashboard
- Some sources (like Finnhub) require symbol to be in their database

---

## Questions?

If you encounter issues with any data source:
1. Check the provider's status page
2. Verify your API key hasn't expired
3. Review rate limits
4. Check the error messages in the tool output

The beauty of this multi-source approach: if one fails, you still have 8 others!
