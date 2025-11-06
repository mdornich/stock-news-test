"""
Source value analytics - Track which data sources provide the most valuable insights
"""

from typing import List, Dict
from collections import defaultdict
from gatherers import NewsArticle
from config import DATA_SOURCES


def analyze_source_value(news_articles: List[NewsArticle]) -> Dict:
    """
    Analyze which data sources provided the most valuable information

    Args:
        news_articles: List of all news articles collected

    Returns:
        Dictionary with source analytics
    """
    if not news_articles:
        return {
            "total_articles": 0,
            "sources": {},
            "high_value_sources": [],
        }

    # Group articles by data source
    by_source = defaultdict(list)
    for article in news_articles:
        by_source[article.data_source_type].append(article)

    # Calculate metrics for each source
    source_metrics = {}

    for source_name, articles in by_source.items():
        total_articles = len(articles)

        # Calculate average weight (indicates recency/value)
        avg_weight = sum(a.weight for a in articles) / total_articles if total_articles > 0 else 0

        # Count high-weight articles (weight >= 0.7)
        high_weight_count = sum(1 for a in articles if a.weight >= 0.7)

        # Calculate percentage of high-weight articles
        high_weight_pct = (high_weight_count / total_articles * 100) if total_articles > 0 else 0

        # Get source metadata
        source_meta = DATA_SOURCES.get(source_name, {})

        source_metrics[source_name] = {
            "total_articles": total_articles,
            "avg_weight": round(avg_weight, 3),
            "high_weight_count": high_weight_count,
            "high_weight_percentage": round(high_weight_pct, 1),
            "cost_tier": source_meta.get("cost", "unknown"),
            "latency": source_meta.get("latency", "unknown"),
            "api_limit": source_meta.get("limit", "unknown"),
        }

    # Sort sources by value (average weight * article count)
    sorted_sources = sorted(
        source_metrics.items(),
        key=lambda x: x[1]["avg_weight"] * x[1]["total_articles"],
        reverse=True,
    )

    # Identify "high value" sources (avg weight > 0.5 and more than 3 articles)
    high_value_sources = [
        name for name, metrics in sorted_sources
        if metrics["avg_weight"] > 0.5 and metrics["total_articles"] >= 3
    ]

    return {
        "total_articles": len(news_articles),
        "unique_sources": len(by_source),
        "sources": dict(sorted_sources),
        "high_value_sources": high_value_sources,
    }


def generate_source_report(analytics: Dict) -> str:
    """
    Generate a human-readable report of source value

    Args:
        analytics: Output from analyze_source_value()

    Returns:
        Formatted string report
    """
    if analytics["total_articles"] == 0:
        return "No data collected from any sources."

    report = []
    report.append("=" * 80)
    report.append("DATA SOURCE VALUE ANALYSIS")
    report.append("=" * 80)
    report.append("")
    report.append(f"Total Articles Collected: {analytics['total_articles']}")
    report.append(f"Unique Sources Used: {analytics['unique_sources']}")
    report.append("")
    report.append("Source Performance (ranked by value):")
    report.append("-" * 80)
    report.append(f"{'Source':<20} {'Articles':<10} {'Avg Weight':<12} {'High-Value':<12} {'Cost':<10} {'Latency':<12}")
    report.append("-" * 80)

    for source_name, metrics in analytics["sources"].items():
        high_value_str = f"{metrics['high_weight_count']} ({metrics['high_weight_percentage']}%)"

        # Add indicator for high-value sources
        indicator = "★" if source_name in analytics["high_value_sources"] else " "

        report.append(
            f"{indicator} {source_name:<18} "
            f"{metrics['total_articles']:<10} "
            f"{metrics['avg_weight']:<12.3f} "
            f"{high_value_str:<12} "
            f"{metrics['cost_tier']:<10} "
            f"{metrics['latency']:<12}"
        )

    report.append("-" * 80)
    report.append("")
    report.append("★ = High-value source (avg weight > 0.5, 3+ articles)")
    report.append("")
    report.append("INTERPRETATION:")
    report.append("- Higher avg weight = more recent/timely data")
    report.append("- High-value articles = published within 24 hours (weight >= 0.7)")
    report.append("- Consider upgrading to paid tiers for high-value sources")
    report.append("")

    # Recommendations
    if analytics["high_value_sources"]:
        report.append("RECOMMENDED SOURCES TO PRIORITIZE:")
        for source in analytics["high_value_sources"]:
            metrics = analytics["sources"][source]
            if metrics["cost_tier"] == "freemium":
                report.append(f"  • {source}: Consider upgrading to paid tier for more data")
            elif metrics["cost_tier"] == "free":
                report.append(f"  • {source}: Free and valuable - keep using!")
            elif metrics["cost_tier"] == "paid":
                report.append(f"  • {source}: Paid tier providing good value")

    report.append("")

    return "\n".join(report)


def get_source_breakdown_by_recency(news_articles: List[NewsArticle]) -> Dict:
    """
    Show which sources provide data in each recency tier

    Args:
        news_articles: List of all news articles

    Returns:
        Dictionary mapping recency labels to source counts
    """
    breakdown = defaultdict(lambda: defaultdict(int))

    for article in news_articles:
        breakdown[article.recency_label][article.data_source_type] += 1

    return dict(breakdown)
