import json

import httpx
import pytest
import respx
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_snaprender.tools.screenshot import Device, ImageFormat, take_screenshot

BASE = "https://app.snap-render.com"

CAPTURE_JSON = {
    "url": "https://example.com",
    "format": "png",
    "width": 1280,
    "height": 800,
    "image": "data:image/png;base64,iVBORw0KGgo=",
    "size": 45320,
    "cache": "MISS",
    "responseTime": "1234ms",
    "remainingCredits": 49,
}

SIGN_JSON = {
    "signed_url": f"{BASE}/v1/screenshot/render?url=https%3A%2F%2Fexample.com&sig=abc",
    "expires_at": "2026-11-11T10:00:00.000Z",
    "expires_in": 86400,
}


@respx.mock
async def test_take_screenshot_defaults_capture_then_sign(mock_context) -> None:
    capture = respx.post(f"{BASE}/v1/screenshot").mock(
        return_value=httpx.Response(200, json=CAPTURE_JSON)
    )
    sign = respx.post(f"{BASE}/v1/screenshot/sign").mock(
        return_value=httpx.Response(200, json=SIGN_JSON)
    )

    result = await take_screenshot(mock_context, url="https://example.com")

    assert capture.called and sign.called
    req = capture.calls.last.request
    assert req.headers["X-API-Key"] == "sk_live_test_key"
    assert req.headers["User-Agent"].startswith("arcade-snaprender/")
    body = json.loads(req.content)
    assert body == {
        "url": "https://example.com",
        "format": "png",
        "width": 1280,
        "height": 800,
        "full_page": False,
        "quality": 90,
        "delay": 0,
        "dark_mode": False,
        "block_ads": True,
        "block_cookie_banners": True,
        "cache": True,
        "response_type": "json",
    }
    sign_body = json.loads(sign.calls.last.request.content)
    # The signed link uses the same render options so it serves the stored copy
    for key in ("url", "format", "width", "height", "full_page", "quality", "dark_mode"):
        assert sign_body[key] == body[key]
    assert sign_body["expires_in"] == 86400
    assert "cache" not in sign_body and "response_type" not in sign_body

    assert result == {
        "screenshot_url": SIGN_JSON["signed_url"],
        "link_expires_at": SIGN_JSON["expires_at"],
        "page_url": "https://example.com",
        "format": "png",
        "width": 1280,
        "height": 800,
        "size_bytes": 45320,
        "served_from_cache": False,
        "render_time": "1234ms",
        "remaining_credits": 49,
    }
    assert "image_data_uri" not in result


@respx.mock
async def test_take_screenshot_all_options_and_image_data(mock_context) -> None:
    capture = respx.post(f"{BASE}/v1/screenshot").mock(
        return_value=httpx.Response(200, json={**CAPTURE_JSON, "format": "jpeg", "cache": "HIT"})
    )
    sign = respx.post(f"{BASE}/v1/screenshot/sign").mock(
        return_value=httpx.Response(200, json=SIGN_JSON)
    )

    result = await take_screenshot(
        mock_context,
        url="https://example.com/pricing",
        format=ImageFormat.JPEG,
        full_page=True,
        device=Device.IPHONE_15_PRO,
        width=1440,
        height=900,
        dark_mode=True,
        block_ads=False,
        block_cookie_banners=False,
        hide_selectors=".chat-widget,#promo",
        click_selector="#accept",
        delay=1500,
        quality=70,
        include_image_data=True,
        link_expires_in=3600,
    )

    body = json.loads(capture.calls.last.request.content)
    assert body["format"] == "jpeg"
    assert body["full_page"] is True
    assert body["device"] == "iphone_15_pro"
    assert body["width"] == 1440 and body["height"] == 900
    assert body["dark_mode"] is True
    assert body["block_ads"] is False and body["block_cookie_banners"] is False
    assert body["hide_selectors"] == ".chat-widget,#promo"
    assert body["click_selector"] == "#accept"
    assert body["delay"] == 1500 and body["quality"] == 70
    sign_body = json.loads(sign.calls.last.request.content)
    assert sign_body["device"] == "iphone_15_pro"
    assert sign_body["expires_in"] == 3600
    assert result["served_from_cache"] is True
    assert result["image_data_uri"] == CAPTURE_JSON["image"]


@respx.mock
async def test_take_screenshot_pdf(mock_context) -> None:
    capture = respx.post(f"{BASE}/v1/screenshot").mock(
        return_value=httpx.Response(200, json={**CAPTURE_JSON, "format": "pdf"})
    )
    respx.post(f"{BASE}/v1/screenshot/sign").mock(return_value=httpx.Response(200, json=SIGN_JSON))

    result = await take_screenshot(mock_context, url="https://example.com", format=ImageFormat.PDF)

    assert json.loads(capture.calls.last.request.content)["format"] == "pdf"
    assert result["format"] == "pdf"


@respx.mock
async def test_take_screenshot_sign_failure_falls_back_to_image_data(mock_context) -> None:
    respx.post(f"{BASE}/v1/screenshot").mock(return_value=httpx.Response(200, json=CAPTURE_JSON))
    respx.post(f"{BASE}/v1/screenshot/sign").mock(
        return_value=httpx.Response(500, json={"error": {"code": "SERVER_ERROR", "message": "x"}})
    )

    result = await take_screenshot(mock_context, url="https://example.com")

    assert result["screenshot_url"] is None
    assert result["image_data_uri"] == CAPTURE_JSON["image"]
    assert "note" in result


@pytest.mark.parametrize(
    "kwargs",
    [
        {"url": "ftp://example.com"},
        {"url": "example.com"},
        {"url": "https://example.com", "width": 100},
        {"url": "https://example.com", "height": 20000},
        {"url": "https://example.com", "delay": 20000},
        {"url": "https://example.com", "quality": 0},
        {"url": "https://example.com", "link_expires_in": 10},
    ],
)
@respx.mock
async def test_take_screenshot_rejects_bad_input_without_calling_api(mock_context, kwargs) -> None:
    route = respx.post(f"{BASE}/v1/screenshot")
    with pytest.raises(ToolExecutionError):
        await take_screenshot(mock_context, **kwargs)
    assert not route.called


@respx.mock
async def test_take_screenshot_api_error_is_reported(mock_context) -> None:
    respx.post(f"{BASE}/v1/screenshot").mock(
        return_value=httpx.Response(
            400,
            json={"error": {"code": "INVALID_URL", "message": "URL is blocked", "status": 400}},
        )
    )
    with pytest.raises(ToolExecutionError, match="INVALID_URL"):
        await take_screenshot(mock_context, url="https://10.0.0.1")
