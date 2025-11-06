# Stock Catalyst Analyzer

An AI-powered tool that identifies potential catalysts for stock price movements by analyzing recent news, SEC filings, and market data.

## Features

- **Weighted News Analysis**: Fetches news from the past 48 hours with recency weighting (more recent = higher weight)
- **SEC Filing Integration**: Automatically checks for recent SEC filings (8-K, 10-K, 10-Q, etc.)
- **Market Context**: Retrieves current price, volume, and sector information
- **AI-Powered Analysis**: Uses Claude AI to synthesize all data and identify catalysts
- **Detailed Breakdown**: Shows weighted news, filing details, and comprehensive analysis

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

## API Keys Required

### NewsAPI (Free Tier Available)
1. Go to [newsapi.org](https://newsapi.org/)
2. Sign up for a free API key
3. Free tier includes 100 requests/day

### Anthropic API Key
1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Create an API key
3. Add credits to your account

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

The tool provides a detailed breakdown including:

1. **Data Collection Summary**: Overview of gathered news, filings, and market data
2. **Weighted News Breakdown**: Top 15 news articles with recency weights
3. **Claude AI Analysis**:
   - Primary catalysts identified
   - News sentiment analysis
   - Volume and price context
   - SEC filing impact
   - Confidence assessment
   - Executive summary

## Project Structure

```
stock-news-test/
├── main.py           # Entry point and orchestration
├── gatherers.py      # Data gathering (news, SEC, market data)
├── analyzer.py       # Claude AI integration
├── config.py         # Configuration and weighting system
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment variables
└── README.md         # This file
```

## How It Works

1. **Fetch News**: Retrieves articles from NewsAPI for the past 48 hours
2. **Calculate Weights**: Assigns recency weights based on publication time
3. **Check SEC Filings**: Queries SEC EDGAR for recent filings
4. **Get Market Data**: Uses yfinance to fetch current price, volume, and context
5. **AI Analysis**: Sends all weighted data to Claude for comprehensive analysis
6. **Display Results**: Shows detailed breakdown and AI-generated insights

## Configuration

Edit `config.py` to customize:

- `DEFAULT_SYMBOL`: Default stock to analyze
- `NEWS_LOOKBACK_HOURS`: How far back to fetch news (default: 48 hours)
- `SEC_LOOKBACK_DAYS`: How far back to check SEC filings (default: 7 days)
- `WEIGHT_TIERS`: Customize the recency weighting system

## Limitations

- NewsAPI free tier limited to 100 requests/day
- SEC EDGAR API requires proper user agent
- Market data relies on yfinance (unofficial Yahoo Finance API)
- Analysis quality depends on available news and data

## Future Enhancements

- Support for multiple stocks in one run
- Historical trend analysis
- Social media sentiment integration
- Email/Slack notifications for catalyst alerts
- Web dashboard interface

## License

MIT