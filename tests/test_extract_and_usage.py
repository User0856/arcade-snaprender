import httpx
import pytest
import respx
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_snaprender.tools.extract import ExtractType, extract_content
from arcade_snaprender.tools.usage import get_usage

BASE = "https://app.snap-render.com"

EXTRACT_JSON = {
    "url": "https://example.com",
    "type": "markdown",
    "content": "# Example Domain\n\nThis domain is for use in documentation examples.",
    "wordCount": 10,
    "processingTimeMs": 1200,
}

USAGE_JSON = {
    "plan": "free",
    "period": {"start": "2026-11-01T00:00:00.000Z", "end": "2026-11-30T23:59:59.000Z"},
    "usage": {"screenshots_used": 12, "screenshots_limit": 200, "screenshots_remaining": 188},
}


@respx.mock
async def test_extract_content_defaults_to_markdown(mock_context) -> None:
    route = respx.get(f"{BASE}/v1/extract").mock(
        return_value=httpx.Response(200, json=EXTRACT_JSON)
    )

    result = await extract_content(mock_context, url="https://example.com")

    req = route.calls.last.request
    assert req.headers["X-API-Key"] == "sk_live_test_key"
    params = dict(req.url.params)
    assert params == {
        "url": "https://example.com",
        "type": "markdown",
        "block_ads": "true",
        "block_cookie_banners": "true",
        "delay": "0",
        "max_length": "100000",
    }
    assert result == {
        "url": "https://example.com",
        "type": "markdown",
        "content": EXTRACT_JSON["content"],
        "word_count": 10,
        "processing_time_ms": 1200,
    }


@respx.mock
async def test_extract_content_options(mock_context) -> None:
    route = respx.get(f"{BASE}/v1/extract").mock(
        return_value=httpx.Response(
            200, json={"url": "https://example.com", "type": "links", "content": ["https://a.b"]}
        )
    )

    result = await extract_content(
        mock_context,
        url="https://example.com",
        content_type=ExtractType.LINKS,
        selector="main",
        block_ads=False,
        block_cookie_banners=False,
        delay=500,
        max_length=2000,
    )

    params = dict(route.calls.last.request.url.params)
    assert params["type"] == "links"
    assert params["selector"] == "main"
    assert params["block_ads"] == "false"
    assert params["block_cookie_banners"] == "false"
    assert params["delay"] == "500"
    assert params["max_length"] == "2000"
    assert result["content"] == ["https://a.b"]
    assert result["word_count"] is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"url": "javascript:alert(1)"},
        {"url": "https://example.com", "max_length": 0},
        {"url": "https://example.com", "max_length": 600000},
        {"url": "https://example.com", "delay": -1},
    ],
)
@respx.mock
async def test_extract_rejects_bad_input(mock_context, kwargs) -> None:
    route = respx.get(f"{BASE}/v1/extract")
    with pytest.raises(ToolExecutionError):
        await extract_content(mock_context, **kwargs)
    assert not route.called


@respx.mock
async def test_get_usage(mock_context) -> None:
    route = respx.get(f"{BASE}/v1/usage").mock(return_value=httpx.Response(200, json=USAGE_JSON))

    result = await get_usage(mock_context)

    assert route.calls.last.request.headers["X-API-Key"] == "sk_live_test_key"
    assert result == {
        "plan": "free",
        "period_start": "2026-11-01T00:00:00.000Z",
        "period_end": "2026-11-30T23:59:59.000Z",
        "used": 12,
        "limit": 200,
        "remaining": 188,
    }
