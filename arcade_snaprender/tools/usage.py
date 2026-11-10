from typing import Annotated, Any

from arcade_mcp_server import Context, tool

from arcade_snaprender.client import SECRET_NAME, request
from arcade_snaprender.tools._metadata import READ_WEB


@tool(requires_secrets=[SECRET_NAME], metadata=READ_WEB)
async def get_usage(
    context: Context,
) -> Annotated[dict[str, Any], "Plan, captures used and left, and the billing period"]:
    """Show the SnapRender plan, how many captures were used this month and how many are left.

    Screenshots and content extractions share one monthly allowance. This call is free.
    """
    data = await request(context, "GET", "/v1/usage")
    period = data.get("period") or {}
    usage = data.get("usage") or {}
    return {
        "plan": data.get("plan"),
        "period_start": period.get("start"),
        "period_end": period.get("end"),
        "used": usage.get("screenshots_used"),
        "limit": usage.get("screenshots_limit"),
        "remaining": usage.get("screenshots_remaining"),
    }
