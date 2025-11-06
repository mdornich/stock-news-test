"""
Claude-powered analysis of stock movements and catalysts
"""

from typing import List, Dict, Optional
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY
from gatherers import NewsArticle


def build_analysis_prompt(
    symbol: str,
    company_name: str,
    news_articles: List[NewsArticle],
    sec_filings: List[Dict],
    market_data: Optional[Dict],
) -> str:
    """
    Build the prompt for Claude to analyze the stock movement

    Args:
        symbol: Stock ticker symbol
        company_name: Company name
        news_articles: List of weighted news articles
        sec_filings: List of recent SEC filings
        market_data: Market data dictionary

    Returns:
        Formatted prompt string
    """
    prompt = f"""You are a financial analyst tasked with identifying potential catalysts for stock price movements.

# Stock Information
Symbol: ${symbol}
Company: {company_name}
"""

    # Add market data context
    if market_data:
        prompt += f"""
# Current Market Context
- Current Price: ${market_data['current_price']}
- Price Change: ${market_data['price_change']} ({market_data['price_change_pct']:+.2f}%)
- Volume: {market_data['volume']:,} (vs avg: {market_data['avg_volume']:,})
- Volume Ratio: {market_data['volume_ratio']}x average
- Sector: {market_data['sector']}
- Industry: {market_data['industry']}
"""

    # Add weighted news articles
    if news_articles:
        prompt += f"""
# News Articles (Past 48 Hours)
Note: Each article has a recency weight (1.0 = most recent/relevant, lower = older).
Pay more attention to higher-weighted articles as they're more likely to be driving current movements.

"""
        for i, article in enumerate(news_articles[:20], 1):  # Limit to top 20
            prompt += f"""
## Article {i} [Weight: {article.weight}, {article.recency_label}]
**Source:** {article.source}
**Published:** {article.published_at.strftime('%Y-%m-%d %H:%M UTC')}
**Title:** {article.title}
**Description:** {article.description or 'N/A'}
**URL:** {article.url}

"""
    else:
        prompt += "\n# News Articles\nNo relevant news articles found in the past 48 hours.\n"

    # Add SEC filings
    if sec_filings:
        prompt += "\n# Recent SEC Filings\n"
        for filing in sec_filings:
            prompt += f"- {filing['type']}: {filing['description']} (Filed: {filing['date']})\n"
            prompt += f"  URL: {filing['url']}\n"
    else:
        prompt += "\n# Recent SEC Filings\nNo recent SEC filings found.\n"

    # Add analysis instructions
    prompt += """
# Your Task

Analyze the above information and provide a comprehensive assessment of potential stock price catalysts.

Please structure your response as follows:

## 1. Primary Catalysts Identified
List and explain any clear catalysts driving the stock movement. Consider:
- Earnings announcements or guidance
- Product launches or updates
- Regulatory news or approvals
- Market-moving partnerships or deals
- Sector-wide movements
- Macroeconomic factors

## 2. News Sentiment Analysis
Summarize the overall sentiment from the weighted news articles:
- What themes emerge from the highest-weighted (most recent) news?
- Is the sentiment primarily positive, negative, or mixed?
- Are there conflicting narratives?

## 3. Volume & Price Context
Based on the volume and price data:
- Is the current volume unusual?
- Does the price movement align with the news sentiment?
- Are there any technical factors worth noting?

## 4. SEC Filing Impact
If any SEC filings are present:
- Do they contain material information?
- How might they be influencing the stock?

## 5. Confidence Assessment
Rate your confidence in identifying clear catalysts:
- HIGH: Clear, obvious catalyst(s) present
- MEDIUM: Probable catalysts identified but with some uncertainty
- LOW: No clear catalyst; movement may be technical or sector-driven

## 6. Summary
Provide a concise 2-3 sentence summary for an investor asking: "Why is this stock moving?"

---

Be specific, cite the news articles and data when possible, and be honest if there's no clear catalyst identified.
"""

    return prompt


def analyze_with_claude(
    symbol: str,
    company_name: str,
    news_articles: List[NewsArticle],
    sec_filings: List[Dict],
    market_data: Optional[Dict],
) -> str:
    """
    Send all gathered data to Claude for analysis

    Args:
        symbol: Stock ticker symbol
        company_name: Company name
        news_articles: List of weighted news articles
        sec_filings: List of recent SEC filings
        market_data: Market data dictionary

    Returns:
        Claude's analysis as a string
    """
    if not ANTHROPIC_API_KEY:
        return "Error: ANTHROPIC_API_KEY not found in environment variables"

    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = build_analysis_prompt(
            symbol=symbol,
            company_name=company_name,
            news_articles=news_articles,
            sec_filings=sec_filings,
            market_data=market_data,
        )

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    except Exception as e:
        return f"Error during Claude analysis: {e}"
