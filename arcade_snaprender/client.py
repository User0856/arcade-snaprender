"""Small HTTP helper shared by the SnapRender tools."""

from typing import Any

import httpx
from arcade_mcp_server import Context
from arcade_mcp_server.exceptions import (
    ToolExecutionError,
    UpstreamError,
    UpstreamRateLimitError,
)

from arcade_snaprender import __version__

BASE_URL = "https://app.snap-render.com"
SECRET_NAME = "SNAPRENDER_API_KEY"  # noqa: S105 (the secret's name, not its value)
SIGNUP_URL = "https://app.snap-render.com/auth/signup"
USER_AGENT = f"arcade-snaprender/{__version__}"

# A full-page capture with a 10 second delay can take a while; stay above the server's own limit.
TIMEOUT = httpx.Timeout(120.0, connect=15.0)


def get_api_key(context: Context) -> str:
    try:
        key = context.get_secret(SECRET_NAME)
    except Exception as exc:
        raise ToolExecutionError(
            f"The {SECRET_NAME} secret is not set. Add your SnapRender API key as a secret "
            f"named {SECRET_NAME} (a free key is available at {SIGNUP_URL}).",
            developer_message=str(exc),
        ) from exc
    if not key:
        raise ToolExecutionError(
            f"The {SECRET_NAME} secret is empty. Add your SnapRender API key as a secret "
            f"named {SECRET_NAME} (a free key is available at {SIGNUP_URL})."
        )
    return key


def require_http_url(url: str) -> None:
    if not url.lower().startswith(("http://", "https://")):
        raise ToolExecutionError(
            f"'{url}' is not a web address. Pass a full URL starting with https:// or http://."
        )


def require_range(name: str, value: int, low: int, high: int) -> None:
    if not low <= value <= high:
        raise ToolExecutionError(f"{name} must be between {low} and {high} (got {value}).")


def _error_details(response: httpx.Response) -> tuple[str, str]:
    try:
        payload = response.json()
        err = payload.get("error", {}) if isinstance(payload, dict) else {}
        code = str(err.get("code") or "HTTP_ERROR")
        message = str(err.get("message") or response.reason_phrase)
    except ValueError:
        code, message = "HTTP_ERROR", (response.text[:300] or response.reason_phrase)
    return code, message


def raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    status = response.status_code
    code, message = _error_details(response)
    text = f"SnapRender API error {status} {code}: {message}"

    if status == 401:
        raise UpstreamError(
            f"SnapRender rejected the API key ({code}). Check the {SECRET_NAME} secret.",
            developer_message=text,
            status_code=status,
        )
    if status == 429 and code != "QUOTA_EXCEEDED":
        retry_after = response.headers.get("Retry-After", "")
        retry_ms = int(retry_after) * 1000 if retry_after.isdigit() else 10_000
        raise UpstreamRateLimitError(text, retry_after_ms=retry_ms, developer_message=text)

    error = UpstreamError(text, developer_message=text, status_code=status)
    if code == "QUOTA_EXCEEDED":
        # The monthly allowance is used up; retrying before the reset only fails again.
        error.can_retry = False
    raise error


async def request(
    context: Context,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    api_key = get_api_key(context)
    headers = {
        "X-API-Key": api_key,
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.request(method, path, params=params, json=json, headers=headers)
    except httpx.TimeoutException as exc:
        raise UpstreamError(
            "SnapRender did not answer in time. Try again, or use a smaller capture.",
            developer_message=repr(exc),
            status_code=504,
        ) from exc
    except httpx.HTTPError as exc:
        raise UpstreamError(
            "Could not reach SnapRender.",
            developer_message=repr(exc),
            status_code=503,
        ) from exc

    raise_for_status(response)
    data: dict[str, Any] = response.json()
    return data


def bool_param(value: bool) -> str:
    return "true" if value else "false"
