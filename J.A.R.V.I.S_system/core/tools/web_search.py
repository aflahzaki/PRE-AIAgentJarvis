"""
Web Search Tools - DuckDuckGo search capabilities for J.A.R.V.I.S agents.

Provides web search, news search, and page summary functionality
using the DuckDuckGo search engine (no API key required).
All functions return structured dict results with success/error status.

Dependencies:
    - duckduckgo-search: Install with `pip install duckduckgo-search`
    - requests: Install with `pip install requests`
"""

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Graceful import of duckduckgo-search
try:
    from duckduckgo_search import DDGS

    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning(
        "duckduckgo-search not installed. Web search features are disabled. "
        "Install with: pip install duckduckgo-search"
    )

# Graceful import of requests
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning(
        "requests not installed. Page summary feature is disabled. "
        "Install with: pip install requests"
    )


def search_web(
    query: str, max_results: int = 5
) -> Dict[str, Union[bool, str, List[Dict[str, str]]]]:
    """Search the web using DuckDuckGo.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (default: 5).

    Returns:
        Dict with 'success' and 'results' list (each with title, url, snippet)
        or 'error' key on failure.
    """
    if not DDGS_AVAILABLE:
        return {
            "success": False,
            "error": "duckduckgo-search not installed. "
            "Install with: pip install duckduckgo-search",
        }

    if not query or not query.strip():
        return {"success": False, "error": "Search query cannot be empty."}

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))

        results = []
        for item in raw_results:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("href", item.get("link", "")),
                "snippet": item.get("body", item.get("snippet", "")),
            })

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
        }

    except Exception as e:
        logger.error("Web search error for query '%s': %s", query, str(e))
        return {
            "success": False,
            "error": "Search failed: {}".format(str(e)),
        }


def search_news(
    query: str, max_results: int = 5
) -> Dict[str, Union[bool, str, List[Dict[str, str]]]]:
    """Search news articles using DuckDuckGo.

    Args:
        query: News search query string.
        max_results: Maximum number of results to return (default: 5).

    Returns:
        Dict with 'success' and 'results' list (each with title, url, snippet,
        date, source) or 'error' key on failure.
    """
    if not DDGS_AVAILABLE:
        return {
            "success": False,
            "error": "duckduckgo-search not installed. "
            "Install with: pip install duckduckgo-search",
        }

    if not query or not query.strip():
        return {"success": False, "error": "Search query cannot be empty."}

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.news(query, max_results=max_results))

        results = []
        for item in raw_results:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", item.get("link", "")),
                "snippet": item.get("body", item.get("snippet", "")),
                "date": item.get("date", ""),
                "source": item.get("source", ""),
            })

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
        }

    except Exception as e:
        logger.error("News search error for query '%s': %s", query, str(e))
        return {
            "success": False,
            "error": "News search failed: {}".format(str(e)),
        }


def get_page_summary(url: str) -> Dict[str, Union[bool, str]]:
    """Get a text summary of a web page.

    Fetches the page content and extracts readable text, truncated
    to a reasonable length for LLM consumption.

    Args:
        url: URL of the page to summarize.

    Returns:
        Dict with 'success', 'url', 'title', and 'content' or 'error' key.
    """
    if not REQUESTS_AVAILABLE:
        return {
            "success": False,
            "error": "requests not installed. "
            "Install with: pip install requests",
        }

    if not url or not url.strip():
        return {"success": False, "error": "URL cannot be empty."}

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        return {
            "success": False,
            "error": "Invalid URL. Must start with http:// or https://",
        }

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return {
                "success": False,
                "error": "Unsupported content type: {}".format(content_type),
            }

        html_content = response.text

        # Extract title from HTML
        title = ""
        if "<title>" in html_content.lower():
            start = html_content.lower().find("<title>") + 7
            end = html_content.lower().find("</title>", start)
            if end > start:
                title = html_content[start:end].strip()

        # Simple HTML to text extraction (remove tags)
        import re

        # Remove script and style elements
        text = re.sub(
            r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL
        )
        text = re.sub(
            r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL
        )
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")

        # Truncate to reasonable length (first 3000 characters)
        max_length = 3000
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated]"

        return {
            "success": True,
            "url": url,
            "title": title,
            "content": text,
            "length": len(text),
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out for URL: {}".format(url),
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Connection error for URL: {}".format(url),
        }
    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": "HTTP error {}: {}".format(
                e.response.status_code if e.response else "unknown", str(e)
            ),
        }
    except Exception as e:
        logger.error("Page summary error for '%s': %s", url, str(e))
        return {
            "success": False,
            "error": "Failed to get page summary: {}".format(str(e)),
        }
