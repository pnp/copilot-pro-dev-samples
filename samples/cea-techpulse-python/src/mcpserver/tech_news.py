from __future__ import annotations

import os
import json
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

from mcp.server.fastmcp import FastMCP

NEWS_API_BASE = "https://newsapi.org/v2"
NEWS_API_KEY = os.environ.get("NEWS_API_KEY") or os.environ.get("SECRET_NEWS_API_KEY") or "DEMO_KEY"
USER_AGENT = "tech-news-mcp-server/1.0"



mcp = FastMCP("tech-news")


def _make_news_api_request(endpoint: str, params: dict | None = None) -> dict:
    """Make a request to the News API."""
    if not NEWS_API_KEY or NEWS_API_KEY == "DEMO_KEY":
        raise RuntimeError("News API key is required. Get your free API key from https://newsapi.org/")

    query_params = {"apiKey": NEWS_API_KEY}
    if params:
        for k, v in params.items():
            if v is not None:
                query_params[k] = str(v)

    url = f"{NEWS_API_BASE}/{endpoint}?{urlencode(query_params)}"
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})

    try:
        with urlopen(req) as resp:  
            return json.loads(resp.read().decode())
    except HTTPError as exc:
        raise RuntimeError(f"News API error: {exc.code} - {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc


def _format_article(article: dict, index: int) -> str:
    """Format a single news article for display."""
    try:
        published = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
        published_str = published.strftime("%a, %b %d, %Y %I:%M %p")
    except (ValueError, KeyError):
        published_str = "Unknown"

    source_name = article.get("source", {}).get("name", "Unknown")
    return "\n".join([
        f"{index}. {article.get('title', 'No title')}",
        f"Source: {source_name}",
        f"Published: {published_str}",
        f"Description: {article.get('description') or 'No description available'}",
        f"URL: {article.get('url', '')}",
        "---",
    ])


def _date_from_timeframe(timeframe: str) -> str:
    """Return an ISO date string for the start of the given timeframe."""
    now = datetime.utcnow()
    if timeframe == "today":
        delta = timedelta(days=1)
    elif timeframe == "month":
        delta = timedelta(days=30)
    else:  # week
        delta = timedelta(days=7)
    return (now - delta).strftime("%Y-%m-%d")



TECH_QUERIES = {
    "general": "technology OR tech OR software OR hardware OR startup",
    "ai": "artificial intelligence OR machine learning OR AI OR ChatGPT OR OpenAI",
    "startups": "startup OR venture capital OR funding OR IPO OR tech company",
    "cybersecurity": "cybersecurity OR hacking OR data breach OR security OR malware",
    "mobile": "smartphone OR iPhone OR Android OR mobile app OR tablet",
    "gaming": "gaming OR video games OR esports OR PlayStation OR Xbox OR Nintendo",
}

TECH_DOMAINS = (
    "techcrunch.com,theverge.com,arstechnica.com,wired.com,"
    "engadget.com,venturebeat.com,zdnet.com,cnet.com,recode.net,mashable.com"
)

SEARCH_DOMAINS = TECH_DOMAINS + ",reuters.com,bloomberg.com"
COMPANY_DOMAINS = SEARCH_DOMAINS + ",cnbc.com"


@mcp.tool()
def get_tech_news(
    category: str = "general",
    limit: int = 10,
    country: str = "us",
) -> str:
    """Get latest technology news headlines.

    Args:
        category: Tech category – general, ai, startups, cybersecurity, mobile, or gaming.
        limit: Number of articles (1-20).
        country: Two-letter country code (e.g. us, gb).
    """
    limit = max(1, min(20, limit))
    query = TECH_QUERIES.get(category, TECH_QUERIES["general"])

    try:
        data = _make_news_api_request("everything", {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": limit,
            "domains": TECH_DOMAINS,
        })
    except RuntimeError as exc:
        return f"Failed to get tech news: {exc}"

    articles = data.get("articles") or []
    if not articles:
        return f"No tech news found for category: {category}"

    formatted = [_format_article(a, i + 1) for i, a in enumerate(articles[:limit])]
    return f"Latest Tech News - {category.upper()} ({len(articles)} articles):\n\n" + "\n".join(formatted)



@mcp.tool()
def search_tech_news(
    keyword: str,
    limit: int = 10,
    timeframe: str = "week",
) -> str:
    """Search for specific tech news by keyword.

    Args:
        keyword: Keyword to search for.
        limit: Number of articles (1-20).
        timeframe: today, week, or month.
    """
    limit = max(1, min(20, limit))
    from_date = _date_from_timeframe(timeframe)
    to_date = datetime.utcnow().strftime("%Y-%m-%d")
    enhanced_query = f"({keyword}) AND (technology OR tech OR software OR startup OR AI OR cybersecurity)"

    try:
        data = _make_news_api_request("everything", {
            "q": enhanced_query,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": limit,
            "from": from_date,
            "to": to_date,
            "domains": SEARCH_DOMAINS,
        })
    except RuntimeError as exc:
        return f"Failed to search tech news: {exc}"

    articles = data.get("articles") or []
    if not articles:
        return f"No tech news found for keyword: {keyword} in timeframe: {timeframe}"

    formatted = [_format_article(a, i + 1) for i, a in enumerate(articles[:limit])]
    return (
        f'Tech News Search Results for "{keyword}" ({timeframe}):\n'
        f"Found {len(articles)} articles\n\n" + "\n".join(formatted)
    )


@mcp.tool()
def get_trending_tech(
    region: str = "us",
    limit: int = 10,
) -> str:
    """Get trending technology topics and headlines.

    Args:
        region: Region code – us, gb, ca, or au.
        limit: Number of articles (1-15).
    """
    limit = max(1, min(15, limit))

    try:
        data = _make_news_api_request("top-headlines", {
            "category": "technology",
            "country": region,
            "pageSize": limit,
        })
    except RuntimeError as exc:
        return f"Failed to get trending tech topics: {exc}"

    articles = data.get("articles") or []
    if not articles:
        return f"No trending tech topics found for region: {region}"

    formatted = [_format_article(a, i + 1) for i, a in enumerate(articles[:limit])]
    return (
        f"Trending Tech Topics ({region.upper()}) - {len(articles)} articles:\n\n"
        + "\n".join(formatted)
    )



@mcp.tool()
def get_company_news(
    company: str,
    limit: int = 8,
    timeframe: str = "week",
) -> str:
    """Get news about a specific tech company.

    Args:
        company: Company name (e.g. Microsoft, Apple, Google).
        limit: Number of articles (1-15).
        timeframe: today, week, or month.
    """
    limit = max(1, min(15, limit))
    from_date = _date_from_timeframe(timeframe)

    try:
        data = _make_news_api_request("everything", {
            "q": f'"{company}"',
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": limit,
            "from": from_date,
            "domains": COMPANY_DOMAINS,
        })
    except RuntimeError as exc:
        return f"Failed to get company news: {exc}"

    articles = data.get("articles") or []
    if not articles:
        return f"No recent news found for company: {company} in timeframe: {timeframe}"

    formatted = [_format_article(a, i + 1) for i, a in enumerate(articles[:limit])]
    return (
        f"{company} News ({timeframe}) - {len(articles)} articles:\n\n"
        + "\n".join(formatted)
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
