# Stock Catalyst Analyzer

An AI-powered tool that identifies potential catalysts for stock price movements by analyzing data from **9 different sources** including news, social media, SEC filings, and market data.

## Features

- **Multi-Source News Aggregation**: Gathers news from 6+ sources (NewsAPI, Finnhub, Alpha Vantage, Google News, Reddit, StockTwits)
- **Weighted Recency System**: Recent news gets higher priority (48-hour sliding window)
- **Social Sentiment Analysis**: Tracks Reddit (r/wallstreetbets, r/stocks) and StockTwits for retail sentiment
- **SEC Filing Monitor**: Detects material events (8-K), insider trading (Form 4), and quarterly/annual reports
- **Options Flow Analysis**: Monitors put/call ratios and unusual options activity
- **Source Value Analytics**: Shows which data sources provide the most timely/valuable information
- **AI-Powered Synthesis**: Claude AI analyzes all data to identify primary catalysts
- **Sentiment Tracking**: Captures sentiment scores from multiple sources when available

## Recency Weighting System

News articles are weighted based on how recent they are:

- **0-12 hours**: Weight 1.0 (Very Recent) - Highest priority
- **12-24 hours**: Weight 0.7 (Recent)
- **24-36 hours**: Weight 0.4 (Moderately Recent)
- **36-48 hours**: Weight 0.2 (Older)

This helps Claude prioritize the most recent events that are likely driving current price movements.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd stock-news-test
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API keys:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Data Sources

The tool aggregates data from 9 different sources:

| Source | Cost | Setup Required | Latency | Value |
|--------|------|----------------|---------|-------|
| **NewsAPI** | Free/Paid | ✅ API Key | Minutes | Broad news coverage |
| **Finnhub** | Free/Paid | ✅ API Key | Seconds | Real-time financial news + sentiment |
| **Alpha Vantage** | Free/Paid | ✅ API Key | Minutes | News sentiment analysis |
| **Google News** | Free | ❌ None | Minutes | Quick aggregation, no setup |
| **Reddit** | Free | ✅ OAuth | Real-time | Retail investor sentiment |
| **StockTwits** | Free | ❌ None | Real-time | Social sentiment (Bullish/Bearish) |
| **SEC EDGAR** | Free | ❌ None | Hours | Official filings, insider trading |
| **Yahoo Finance** | Free | ❌ None | Minutes | Market data, options, earnings |
| **Twitter/X** | Paid | ❌ Skip | Real-time | (Not recommended - expensive API) |

**📖 Detailed Setup Guide**: See [DATA_SOURCES_GUIDE.md](DATA_SOURCES_GUIDE.md) for step-by-step instructions for each source.

### Minimum Setup (Start Here)

**Only ONE API key is truly required:**
- ✅ **Anthropic API** ([Get it here](https://console.anthropic.com/))

**Three sources work without any setup:**
- ✅ Google News (RSS feeds)
- ✅ StockTwits (public API)
- ✅ SEC EDGAR (public API)
- ✅ Yahoo Finance (yfinance library)

### Recommended Setup (Better Results)

Add these free API keys for significantly better catalyst detection:
1. **Finnhub** ([Sign up](https://finnhub.io/register)) - 2 min setup, very timely
2. **NewsAPI** ([Sign up](https://newsapi.org/)) - 2 min setup, broad coverage
3. **Reddit** ([Create app](https://www.reddit.com/prefs/apps)) - 5 min setup, retail sentiment

**Result**: With all 3 recommended sources, you'll have **7 out of 9 data sources** active!

## Usage

### Default Usage (NVIDIA)
```bash
python main.py
```

### Custom Stock Symbol
```bash
python main.py AAPL "Apple Inc"
```

### Examples
```bash
# Tesla
python main.py TSLA Tesla

# Microsoft
python main.py MSFT Microsoft

# Amazon
python main.py AMZN Amazon
```

## Output

The tool provides a comprehensive multi-section analysis:

### 1. Data Collection Summary
- Total articles collected from each source
- Recency distribution (Very Recent, Recent, Moderately Recent, Older)
- Source distribution (which sources contributed how many articles)
- SEC filings detected (8-K, 10-Q, 10-K, Form 4)
- Insider trading activity
- Market data (price change, volume ratio)
- Options activity (put/call ratio)

### 2. Data Source Value Report ⭐ NEW
- **Source Performance Rankings**: Which sources provided the most valuable data
- **Average Weight by Source**: Timeliness of each data source
- **High-Value Article Count**: Articles published in last 24 hours per source
- **Cost Analysis**: Free vs. paid tier indicators
- **Recommendations**: Which paid sources are worth upgrading

Example output:
```
Source Performance (ranked by value):
Source          Articles  Avg Weight  High-Value  Cost    Latency
----------------------------------------------------------------
★ Finnhub       15        0.850       12 (80%)    free    seconds
★ Reddit        8         0.725       6 (75%)     free    real-time
★ NewsAPI       20        0.650       10 (50%)    free    minutes
```

### 3. Weighted News Breakdown
- Top 15 articles with recency weights
- Source attribution (e.g., "Reuters via Finnhub")
- Sentiment indicators (🟢 Positive, 🔴 Negative, ⚪ Neutral)
- Hours since publication
- Article descriptions

### 4. Claude AI Analysis
- **Primary Catalysts**: Clear drivers of price movement
- **News Sentiment**: Overall tone and themes
- **Volume & Price Context**: Technical analysis
- **SEC Filing Impact**: Material events and insider activity
- **Confidence Rating**: HIGH/MEDIUM/LOW based on clarity of catalysts
- **Executive Summary**: 2-3 sentence answer to "Why is this stock moving?"

## Project Structure

```
stock-news-test/
├── main.py                  # Entry point and orchestration
├── gatherers.py             # Multi-source data gathering (9 sources)
├── analyzer.py              # Claude AI integration
├── source_analytics.py      # Source value analysis and reporting
├── config.py                # Configuration, API keys, weighting system
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
├── DATA_SOURCES_GUIDE.md    # Detailed setup guide for all 9 sources
└── README.md                # This file
```

## How It Works

### Data Gathering (Multi-Source Aggregation)
1. **News Aggregation**: Fetches from NewsAPI, Finnhub, Alpha Vantage, Google News
2. **Social Sentiment**: Scrapes Reddit (WSB, stocks, investing) and StockTwits
3. **SEC Filings**: Queries EDGAR for 8-K, 10-K, 10-Q, Form 4 filings
4. **Market Data**: Uses yfinance for price, volume, options, earnings calendar
5. **Deduplication**: Removes duplicate articles across sources
6. **Recency Weighting**: Assigns 0.2-1.0 weights based on publication time

### Analysis Pipeline
7. **Source Analytics**: Calculates which sources provided the most valuable data
8. **Sentiment Aggregation**: Combines sentiment scores from multiple sources
9. **AI Synthesis**: Claude analyzes all weighted data for catalyst identification
10. **Multi-Section Output**: Displays source value report, weighted news, and AI insights

## Configuration

Edit `config.py` to customize:

- `DEFAULT_SYMBOL`: Default stock to analyze
- `NEWS_LOOKBACK_HOURS`: How far back to fetch news (default: 48 hours)
- `SEC_LOOKBACK_DAYS`: How far back to check SEC filings (default: 7 days)
- `WEIGHT_TIERS`: Customize the recency weighting system

## Understanding the Source Value Report

After each run, you'll see which data sources performed best:

**What the metrics mean:**
- **Avg Weight**: Higher = more timely data (0.7+ is excellent)
- **High-Value %**: Percentage of articles from last 24 hours
- **★ Symbol**: Indicates a high-performing source worth using/upgrading

**How to use this data:**
1. Run the tool 3-5 times on different stocks
2. Note which sources consistently rank high
3. For high-value **freemium** sources, consider upgrading to paid tier
4. For low-value paid sources, consider downgrading or canceling

## Rate Limits & Constraints

| Source | Free Tier Limit | Constraint |
|--------|----------------|------------|
| NewsAPI | 100/day | Daily cap, upgrade for more |
| Finnhub | 60/min | Rate limit, rarely hit |
| Alpha Vantage | 5/min, 500/day | Slowest free tier |
| Google News | Unlimited | RSS parsing can be flaky |
| Reddit | 60/min | OAuth refresh needed |
| StockTwits | 200/hour | Generous, rarely hit |
| SEC EDGAR | 10/second | Very generous |
| Yahoo Finance | 2000/hour | Via yfinance, unofficial |

## Known Limitations

- **Duplicate Detection**: May occasionally show near-duplicate articles from different sources
- **Sentiment Accuracy**: Automated sentiment can misread sarcasm or complex language
- **Reddit Rate Limits**: OAuth token expires, may need to re-authenticate
- **yfinance Reliability**: Unofficial API, can break if Yahoo changes structure
- **Alpha Vantage Speed**: 5 calls/min on free tier is quite slow

## Troubleshooting

**"Info: [SOURCE] not found, skipping"**
- Normal behavior - source doesn't have API key configured
- Tool gracefully continues with other sources

**Rate limit errors**
- Wait 1 minute and try again
- Consider upgrading to paid tier for that source
- Or run less frequently

**No high-value articles found**
- Stock may not have recent news/catalysts
- Try during market hours or after earnings
- Add more data sources for better coverage

## Future Enhancements

Potential additions:
- [ ] Historical catalyst tracking (what drove past movements)
- [ ] Multi-stock batch analysis
- [ ] Email/Slack/Discord notifications for new catalysts
- [ ] Web dashboard interface
- [ ] Export to PDF/JSON
- [ ] Customizable alert thresholds
- [ ] Integration with trading platforms

## License

MIT