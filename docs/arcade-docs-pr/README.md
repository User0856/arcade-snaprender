# Arcade docs listing draft

Files for a SnapRender page in the Arcade MCP server catalog (docs.arcade.dev/en/resources/integrations), in the format of the `ArcadeAI/docs` repository (Fumadocs, MDX under `content/docs/`). It follows the existing Partner pages for Nimble and Tavily.

| File here | Path in ArcadeAI/docs |
| --- | --- |
| `content/docs/resources/integrations/search/snaprender.mdx` | same path |
| `data/partner-toolkits.snippet.ts` | append the entry to `PARTNER_TOOLKITS` in `data/partner-toolkits.ts` |
| `public/images/partners/snaprender.png` | same path |
| (one line) | add `"snaprender"` under `"---Partners---"` in `content/docs/resources/integrations/search/meta.json` |

Status (November 2026): the `ArcadeAI/docs` repository was archived on Oct 26 2026, so it no longer accepts pull requests. The old "Contribute a server" page now redirects to the Arcade Registry early access page, and Partner pages are added by the Arcade team.

## PR or message text

Title: Add SnapRender as a Partner MCP server

SnapRender captures screenshots and PDFs of public web pages and reads pages as markdown, in a real Chrome browser. This adds a Partner page under Search, next to Nimble and Tavily.

- Remote MCP server: https://app.snap-render.com/mcp (Streamable HTTP). Auth is an API key in an `X-API-Key` header, stored as an Arcade header secret, the same pattern as the Nimble page.
- Arcade tool package: `arcade_snaprender` on PyPI, built with arcade-mcp, MIT: https://github.com/User0856/arcade-snaprender
- Free plan: 200 captures a month, no card.

Tested: the hosted server answers `initialize` and `tools/list` with the `X-API-Key` header, and the tool package passes its tests and a live run against the API.
