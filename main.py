#!/usr/bin/env python3
"""
Stock Explainer - Identify catalysts for stock price movements

This tool gathers news, SEC filings, and market data, then uses Claude AI
to analyze potential catalysts driving stock movements.
"""

import sys
from datetime import datetime
from config import DEFAULT_SYMBOL, DEFAULT_COMPANY_NAME
from gatherers import (
    aggregate_all_news,
    fetch_sec_filings,
    fetch_market_data,
    fetch_insider_trades,
    fetch_earnings_and_options,
)
from analyzer import analyze_with_claude
from source_analytics import analyze_source_value, generate_source_report


def print_header():
    """Print the application header"""
    print("=" * 80)
    print("STOCK CATALYST ANALYZER")
    print("=" * 80)
    print()


def print_section_header(title: str):
    """Print a section header"""
    print("\n" + "─" * 80)
    print(f"  {title}")
    print("─" * 80 + "\n")


def print_data_summary(news_articles, sec_filings, market_data, insider_trades, earnings_options):
    """Print a summary of the gathered data"""
    print_section_header("DATA COLLECTION SUMMARY")

    print(f"📰 News Articles: {len(news_articles)} articles found")
    if news_articles:
        print(f"   └─ Date Range: {news_articles[-1].published_at.strftime('%Y-%m-%d %H:%M')} to "
              f"{news_articles[0].published_at.strftime('%Y-%m-%d %H:%M')} UTC")

        # Show weight distribution
        weight_counts = {}
        source_counts = {}
        for article in news_articles:
            label = article.recency_label
            weight_counts[label] = weight_counts.get(label, 0) + 1
            source_counts[article.data_source_type] = source_counts.get(article.data_source_type, 0) + 1

        print(f"   └─ Recency Distribution:")
        for label in ["Very Recent", "Recent", "Moderately Recent", "Older"]:
            count = weight_counts.get(label, 0)
            if count > 0:
                print(f"      • {label}: {count} articles")

        print(f"   └─ Source Distribution:")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"      • {source}: {count} articles")

    print(f"\n📄 SEC Filings: {len(sec_filings)} recent filings")
    if sec_filings:
        for filing in sec_filings[:5]:  # Show top 5
            print(f"   └─ {filing['type']}: {filing['description']} ({filing['date']})")

    if insider_trades:
        print(f"\n👔 Insider Trading: {len(insider_trades)} Form 4 filings detected")
        for trade in insider_trades[:3]:  # Show top 3
            print(f"   └─ {trade['date']}: {trade['description']}")

    if market_data:
        print(f"\n📊 Market Data:")
        print(f"   └─ Price: ${market_data['current_price']} "
              f"({market_data['price_change_pct']:+.2f}%)")
        print(f"   └─ Volume: {market_data['volume']:,} "
              f"({market_data['volume_ratio']:.2f}x avg)")
    else:
        print(f"\n📊 Market Data: Unavailable")

    # Show earnings and options data
    if earnings_options.get("options"):
        opts = earnings_options["options"]
        print(f"\n📈 Options Activity:")
        print(f"   └─ Put/Call Ratio: {opts.get('put_call_ratio', 'N/A')}")
        print(f"   └─ Call Volume: {opts.get('total_call_volume', 0):,}")
        print(f"   └─ Put Volume: {opts.get('total_put_volume', 0):,}")

    print()


def print_detailed_news(news_articles):
    """Print detailed breakdown of news articles with weights and source attribution"""
    print_section_header("WEIGHTED NEWS BREAKDOWN")

    if not news_articles:
        print("No news articles found.\n")
        return

    for i, article in enumerate(news_articles[:15], 1):  # Show top 15
        hours_ago = (datetime.utcnow() - article.published_at).total_seconds() / 3600

        # Show sentiment if available
        sentiment_str = ""
        if article.sentiment is not None:
            if article.sentiment > 0.2:
                sentiment_str = " | Sentiment: 🟢 Positive"
            elif article.sentiment < -0.2:
                sentiment_str = " | Sentiment: 🔴 Negative"
            else:
                sentiment_str = " | Sentiment: ⚪ Neutral"

        print(f"{i}. [{article.recency_label} - Weight: {article.weight}]")
        print(f"   {article.title}")
        print(f"   Source: {article.source} (via {article.data_source_type}) | "
              f"Published: {hours_ago:.1f} hours ago{sentiment_str}")
        print(f"   {article.description[:200] if article.description else 'No description'}...")
        print()


def run_analysis(symbol: str = None, company_name: str = None):
    """
    Main function to run the stock analysis

    Args:
        symbol: Stock ticker symbol (defaults to NVDA)
        company_name: Company name (defaults to NVIDIA)
    """
    # Use defaults if not provided
    symbol = symbol or DEFAULT_SYMBOL
    company_name = company_name or DEFAULT_COMPANY_NAME

    print_header()
    print(f"Analyzing: {company_name} (${symbol})")
    print(f"Analysis Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Step 1: Gather data from all sources
    print("🔍 Gathering data from all sources...")
    news_articles = aggregate_all_news(symbol, company_name)

    print("   └─ Checking SEC filings...")
    sec_filings = fetch_sec_filings(symbol)

    print("   └─ Checking insider trades...")
    insider_trades = fetch_insider_trades(symbol)

    print("   └─ Retrieving market data...")
    market_data = fetch_market_data(symbol)

    print("   └─ Fetching earnings and options data...")
    earnings_options = fetch_earnings_and_options(symbol)

    print("✓ Data collection complete\n")

    # Step 2: Print data summary
    print_data_summary(news_articles, sec_filings, market_data, insider_trades, earnings_options)

    # Step 3: Source value analytics
    print_section_header("DATA SOURCE VALUE REPORT")
    analytics = analyze_source_value(news_articles)
    source_report = generate_source_report(analytics)
    print(source_report)

    # Step 4: Print detailed news breakdown
    print_detailed_news(news_articles)

    # Step 5: Run Claude analysis
    print_section_header("CLAUDE AI ANALYSIS")
    print("🤖 Analyzing data with Claude AI...\n")

    # Combine all SEC data (filings + insider trades)
    all_sec_data = sec_filings + insider_trades

    analysis = analyze_with_claude(
        symbol=symbol,
        company_name=company_name,
        news_articles=news_articles,
        sec_filings=all_sec_data,
        market_data=market_data,
    )

    print(analysis)
    print()

    # Footer
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


def main():
    """Entry point for the application"""
    # Check if symbol and company name provided via command line
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        company_name = sys.argv[2] if len(sys.argv) > 2 else symbol
        run_analysis(symbol, company_name)
    else:
        # Use defaults
        run_analysis()


if __name__ == "__main__":
    main()
