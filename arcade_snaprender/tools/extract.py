from enum import Enum
from typing import Annotated, Any

from arcade_mcp_server import Context, tool

from arcade_snaprender.client import (
    SECRET_NAME,
    bool_param,
    request,
    require_http_url,
    require_range,
)
from arcade_snaprender.tools._metadata import READ_WEB


class ExtractType(str, Enum):
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    ARTICLE = "article"
    LINKS = "links"
    METADATA = "metadata"


@tool(requires_secrets=[SECRET_NAME], metadata=READ_WEB)
async def extract_content(
    context: Context,
    url: Annotated[str, "Public page to read, a full URL starting with https:// or http://"],
    content_type: Annotated[
        ExtractType,
        "What to return: markdown (default, readable page content), text (plain text), "
        "html (rendered HTML), article (title, author, excerpt and main content), "
        "links (every link on the page) or metadata (title, description, Open Graph tags)",
    ] = ExtractType.MARKDOWN,
    selector: Annotated[
        str | None, "CSS selector to read only part of the page, for example 'main' or 'article'"
    ] = None,
    block_ads: Annotated[bool, "Block ads and trackers"] = True,
    block_cookie_banners: Annotated[bool, "Remove cookie consent banners"] = True,
    delay: Annotated[int, "Extra milliseconds to wait after the page loads, 0 to 10000"] = 0,
    max_length: Annotated[int, "Maximum characters of content to return, 1 to 500000"] = 100000,
) -> Annotated[dict[str, Any], "The extracted content and its word count"]:
    """Read a web page as clean markdown, text, HTML, article fields, links or metadata.

    The page is loaded in a real Chrome browser first, so content drawn by JavaScript is
    included. Each extraction uses one credit from the SnapRender monthly allowance.
    Pages behind a login and private networks cannot be read.
    """
    require_http_url(url)
    require_range("delay", delay, 0, 10000)
    require_range("max_length", max_length, 1, 500000)

    params: dict[str, Any] = {
        "url": url,
        "type": ExtractType(content_type).value,
        "block_ads": bool_param(block_ads),
        "block_cookie_banners": bool_param(block_cookie_banners),
        "delay": delay,
        "max_length": max_length,
    }
    if selector:
        params["selector"] = selector

    data = await request(context, "GET", "/v1/extract", params=params)
    return {
        "url": data.get("url", url),
        "type": data.get("type", params["type"]),
        "content": data.get("content"),
        "word_count": data.get("wordCount"),
        "processing_time_ms": data.get("processingTimeMs"),
    }
