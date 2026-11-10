import httpx
import pytest
import respx
from arcade_mcp_server.exceptions import (
    ToolExecutionError,
    UpstreamError,
    UpstreamRateLimitError,
)

from arcade_snaprender.tools.usage import get_usage

BASE = "https://app.snap-render.com"


def _err(code: str, message: str, status: int) -> dict:
    return {"error": {"code": code, "message": message, "status": status}}


@respx.mock
async def test_invalid_key_message_names_the_secret(mock_context) -> None:
    respx.get(f"{BASE}/v1/usage").mock(
        return_value=httpx.Response(401, json=_err("INVALID_API_KEY", "Invalid API key", 401))
    )
    with pytest.raises(UpstreamError) as exc:
        await get_usage(mock_context)
    assert "SNAPRENDER_API_KEY" in exc.value.message
    assert exc.value.status_code == 401


@respx.mock
async def test_rate_limit_uses_retry_after(mock_context) -> None:
    respx.get(f"{BASE}/v1/usage").mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "7"},
            json=_err("RATE_LIMITED", "Too many requests", 429),
        )
    )
    with pytest.raises(UpstreamRateLimitError) as exc:
        await get_usage(mock_context)
    assert exc.value.retry_after_ms == 7000


@respx.mock
async def test_quota_exceeded_is_not_retryable(mock_context) -> None:
    respx.get(f"{BASE}/v1/usage").mock(
        return_value=httpx.Response(
            429, json=_err("QUOTA_EXCEEDED", "Monthly quota of 200 used", 429)
        )
    )
    with pytest.raises(ToolExecutionError) as exc:
        await get_usage(mock_context)
    assert not isinstance(exc.value, UpstreamRateLimitError)
    assert "QUOTA_EXCEEDED" in exc.value.message
    assert exc.value.can_retry is False


@respx.mock
async def test_server_error_without_json_body(mock_context) -> None:
    respx.get(f"{BASE}/v1/usage").mock(return_value=httpx.Response(502, text="Bad gateway"))
    with pytest.raises(UpstreamError) as exc:
        await get_usage(mock_context)
    assert exc.value.status_code == 502
    assert exc.value.can_retry is True


@respx.mock
async def test_timeout_is_reported(mock_context) -> None:
    respx.get(f"{BASE}/v1/usage").mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(UpstreamError) as exc:
        await get_usage(mock_context)
    assert exc.value.status_code == 504


async def test_missing_secret_is_a_clear_error() -> None:
    from unittest.mock import MagicMock

    context = MagicMock()
    context.get_secret = MagicMock(side_effect=ValueError("Secret not found"))
    with pytest.raises(ToolExecutionError, match="SNAPRENDER_API_KEY"):
        await get_usage(context)


def test_tools_register_with_secret_and_metadata() -> None:
    from arcade_core.catalog import ToolCatalog

    import arcade_snaprender

    catalog = ToolCatalog()
    catalog.add_module(arcade_snaprender, "SnapRender")
    names = sorted(t.definition.name for t in catalog)
    assert names == ["ExtractContent", "GetUsage", "TakeScreenshot"]
    for t in catalog:
        secrets = [s.key for s in (t.definition.requirements.secrets or [])]
        assert secrets == ["SNAPRENDER_API_KEY"]
        behavior = t.definition.metadata.behavior
        assert behavior.read_only is True and behavior.open_world is True
