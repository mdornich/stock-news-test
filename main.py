#!/usr/bin/env python3
"""
Stock Explainer - Identify catalysts for stock price movements

This tool gathers news, SEC filings, and market data, then uses Claude AI
to analyze potential catalysts driving stock movements.
"""

import sys
from datetime import datetime
from config import DEFAULT_SYMBOL, DEFAULT_COMPANY_NAME
from gatherers import fetch_news, fetch_sec_filings, fetch_market_data
from analyzer import analyze_with_claude


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


def print_data_summary(news_articles, sec_filings, market_data):
    """Print a summary of the gathered data"""
    print_section_header("DATA COLLECTION SUMMARY")

    print(f"📰 News Articles: {len(news_articles)} articles found")
    if news_articles:
        print(f"   └─ Date Range: {news_articles[-1].published_at.strftime('%Y-%m-%d %H:%M')} to "
              f"{news_articles[0].published_at.strftime('%Y-%m-%d %H:%M')} UTC")

        # Show weight distribution
        weight_counts = {}
        for article in news_articles:
            label = article.recency_label
            weight_counts[label] = weight_counts.get(label, 0) + 1

        print(f"   └─ Recency Distribution:")
        for label in ["Very Recent", "Recent", "Moderately Recent", "Older"]:
            count = weight_counts.get(label, 0)
            if count > 0:
                print(f"      • {label}: {count} articles")

    print(f"\n📄 SEC Filings: {len(sec_filings)} recent filings")
    if sec_filings:
        for filing in sec_filings:
            print(f"   └─ {filing['type']}: {filing['description']} ({filing['date']})")

    if market_data:
        print(f"\n📊 Market Data:")
        print(f"   └─ Price: ${market_data['current_price']} "
              f"({market_data['price_change_pct']:+.2f}%)")
        print(f"   └─ Volume: {market_data['volume']:,} "
              f"({market_data['volume_ratio']:.2f}x avg)")
    else:
        print(f"\n📊 Market Data: Unavailable")

    print()


def print_detailed_news(news_articles):
    """Print detailed breakdown of news articles with weights"""
    print_section_header("WEIGHTED NEWS BREAKDOWN")

    if not news_articles:
        print("No news articles found.\n")
        return

    for i, article in enumerate(news_articles[:15], 1):  # Show top 15
        hours_ago = (datetime.utcnow() - article.published_at).total_seconds() / 3600

        print(f"{i}. [{article.recency_label} - Weight: {article.weight}]")
        print(f"   {article.title}")
        print(f"   Source: {article.source} | Published: {hours_ago:.1f} hours ago")
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

    # Step 1: Gather data
    print("🔍 Gathering data...")
    print("   └─ Fetching news articles...")
    news_articles = fetch_news(symbol, company_name)

    print("   └─ Checking SEC filings...")
    sec_filings = fetch_sec_filings(symbol)

    print("   └─ Retrieving market data...")
    market_data = fetch_market_data(symbol)

    print("✓ Data collection complete\n")

    # Step 2: Print data summary
    print_data_summary(news_articles, sec_filings, market_data)

    # Step 3: Print detailed news breakdown
    print_detailed_news(news_articles)

    # Step 4: Run Claude analysis
    print_section_header("CLAUDE AI ANALYSIS")
    print("🤖 Analyzing data with Claude AI...\n")

    analysis = analyze_with_claude(
        symbol=symbol,
        company_name=company_name,
        news_articles=news_articles,
        sec_filings=sec_filings,
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
