from enum import Enum
from typing import Annotated, Any

from arcade_mcp_server import Context, tool
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_snaprender.client import SECRET_NAME, request, require_http_url, require_range
from arcade_snaprender.tools._metadata import READ_WEB


class ImageFormat(str, Enum):
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"
    PDF = "pdf"


class Device(str, Enum):
    IPHONE_14 = "iphone_14"
    IPHONE_15_PRO = "iphone_15_pro"
    PIXEL_7 = "pixel_7"
    IPAD_PRO = "ipad_pro"
    MACBOOK_PRO = "macbook_pro"


@tool(requires_secrets=[SECRET_NAME], metadata=READ_WEB)
async def take_screenshot(
    context: Context,
    url: Annotated[str, "Public page to capture, a full URL starting with https:// or http://"],
    format: Annotated[
        ImageFormat, "Output format: png (default), jpeg, webp, or pdf"
    ] = ImageFormat.PNG,
    full_page: Annotated[
        bool, "Capture the whole scrollable page instead of only the first screen"
    ] = False,
    device: Annotated[
        Device | None,
        "Phone, tablet or laptop preset. It sets the screen size and user agent and "
        "overrides width and height",
    ] = None,
    width: Annotated[int, "Viewport width in CSS pixels, 320 to 3840"] = 1280,
    height: Annotated[int, "Viewport height in CSS pixels, 200 to 10000"] = 800,
    dark_mode: Annotated[bool, "Ask the page for its dark color scheme"] = False,
    block_ads: Annotated[bool, "Block ads and trackers"] = True,
    block_cookie_banners: Annotated[bool, "Remove cookie consent banners"] = True,
    hide_selectors: Annotated[
        str | None, "Comma-separated CSS selectors to hide before the capture, e.g. '.chat,#promo'"
    ] = None,
    click_selector: Annotated[
        str | None, "CSS selector to click before the capture, e.g. to close a popup"
    ] = None,
    delay: Annotated[int, "Extra milliseconds to wait after the page loads, 0 to 10000"] = 0,
    quality: Annotated[int, "JPEG and WebP quality, 1 to 100. Ignored for png and pdf"] = 90,
    include_image_data: Annotated[
        bool,
        "Also return the file itself as a base64 data URI. It is large, so leave this off "
        "unless code needs the bytes",
    ] = False,
    link_expires_in: Annotated[
        int, "How long the returned screenshot link works, in seconds, 60 to 2592000"
    ] = 86400,
) -> Annotated[dict[str, Any], "Link to the screenshot plus capture details"]:
    """Capture a screenshot or PDF of a web page in a real Chrome browser.

    Returns screenshot_url, a link anyone can open to view or download the file, so it can be
    pasted into a message, document or ticket. Each capture uses one credit from the SnapRender
    monthly allowance. If the same page with the same options was captured in the last 24 hours,
    that copy is returned for free. Pages behind a login and private networks cannot be captured.
    """
    require_http_url(url)
    require_range("width", width, 320, 3840)
    require_range("height", height, 200, 10000)
    require_range("delay", delay, 0, 10000)
    require_range("quality", quality, 1, 100)
    require_range("link_expires_in", link_expires_in, 60, 2592000)

    options: dict[str, Any] = {
        "url": url,
        "format": ImageFormat(format).value,
        "width": width,
        "height": height,
        "full_page": full_page,
        "quality": quality,
        "delay": delay,
        "dark_mode": dark_mode,
        "block_ads": block_ads,
        "block_cookie_banners": block_cookie_banners,
    }
    if device is not None:
        options["device"] = Device(device).value
    if hide_selectors:
        options["hide_selectors"] = hide_selectors
    if click_selector:
        options["click_selector"] = click_selector

    # cache: true stores the capture, so the signed link below serves this exact copy
    # instead of rendering (and charging) again when someone opens it.
    capture = await request(
        context,
        "POST",
        "/v1/screenshot",
        json={**options, "cache": True, "response_type": "json"},
    )

    result: dict[str, Any] = {
        "screenshot_url": None,
        "link_expires_at": None,
        "page_url": capture.get("url", url),
        "format": capture.get("format", options["format"]),
        "width": capture.get("width"),
        "height": capture.get("height"),
        "size_bytes": capture.get("size"),
        "served_from_cache": capture.get("cache") == "HIT",
        "render_time": capture.get("responseTime"),
        "remaining_credits": capture.get("remainingCredits"),
    }

    try:
        signed = await request(
            context,
            "POST",
            "/v1/screenshot/sign",
            json={**options, "expires_in": link_expires_in},
        )
        result["screenshot_url"] = signed.get("signed_url")
        result["link_expires_at"] = signed.get("expires_at")
    except ToolExecutionError as exc:
        # The capture itself worked and was paid for, so hand back the file instead of failing.
        result["note"] = f"The capture worked but a share link could not be created: {exc.message}"
        include_image_data = True

    if include_image_data:
        result["image_data_uri"] = capture.get("image")
    return result
