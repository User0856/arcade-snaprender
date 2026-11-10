from arcade_mcp_server.metadata import (
    Behavior,
    Classification,
    Operation,
    ServiceDomain,
    ToolMetadata,
)

# Every SnapRender tool reads public web pages (or the account's usage) and changes nothing.
READ_WEB: ToolMetadata = ToolMetadata(
    classification=Classification(service_domains=[ServiceDomain.WEB_SCRAPING]),
    behavior=Behavior(
        operations=[Operation.READ],
        read_only=True,
        destructive=False,
        idempotent=True,
        open_world=True,
    ),
)
