import sys
from typing import cast

from arcade_mcp_server import MCPApp
from arcade_mcp_server.mcp_app import TransportType

import arcade_snaprender

app = MCPApp(
    name="SnapRender",
    version=arcade_snaprender.__version__,
    instructions=(
        "Use this server to see or read public web pages. TakeScreenshot captures a page "
        "(or a phone view with device) as an image or PDF and returns a link to it. "
        "ExtractContent reads a page as markdown, text, links or metadata. GetUsage shows "
        "how many captures are left this month."
    ),
)

app.add_tools_from_module(arcade_snaprender)


def main() -> None:
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000

    app.run(transport=cast(TransportType, transport), host=host, port=port)


if __name__ == "__main__":
    main()
