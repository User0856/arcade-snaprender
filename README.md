# arcade-snaprender

[Arcade](https://arcade.dev) tools for [SnapRender](https://snap-render.com), so AI agents can see and read public web pages. Pages load in a real Chrome browser, so content drawn by JavaScript is included.

| Tool | What it does |
| --- | --- |
| `SnapRender.TakeScreenshot` | Captures a page as PNG, JPEG, WebP or PDF (full page, phone or tablet presets, dark mode, hidden elements, click before capture) and returns a link to the file |
| `SnapRender.ExtractContent` | Reads a page as markdown, plain text, HTML, article fields, a list of links, or metadata |
| `SnapRender.GetUsage` | Shows the plan, captures used this month and captures left |

Built with [arcade-mcp](https://github.com/ArcadeAI/arcade-mcp). Works as a local MCP server (stdio or HTTP) or deployed to Arcade Cloud.

## Get an API key

Create a free account at [app.snap-render.com](https://app.snap-render.com/auth/signup). The free plan includes 200 captures a month with no card. Screenshots and extractions share the allowance; failed captures are not counted.

The tools read the key from an Arcade secret named `SNAPRENDER_API_KEY`. The key is never passed to the model.

## Install

```bash
pip install arcade_snaprender
```

or with uv:

```bash
uv pip install arcade_snaprender
```

## Run it

### Local MCP server

Export the key, or put it in a `.env` file in the folder you start the server from:

```bash
echo "SNAPRENDER_API_KEY=sk_live_..." > .env
```

Then start the server over stdio (for Claude Desktop, Cursor and other local clients):

```bash
arcade-snaprender
```

or over HTTP on 127.0.0.1:8000:

```bash
arcade-snaprender http
```

You can also load it with the Arcade CLI, which finds installed `arcade_*` packages:

```bash
arcade mcp --tool-package snaprender
```

### Arcade Cloud

Clone this repository, log in and deploy:

```bash
arcade login
arcade deploy -e arcade_snaprender/__main__.py
```

Then add `SNAPRENDER_API_KEY` under **Secrets** in the [Arcade dashboard](https://app.arcade.dev), or with the CLI:

```bash
arcade secret set SNAPRENDER_API_KEY=sk_live_...
```

## Tools

### TakeScreenshot

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `url` | string | required | Full URL starting with `https://` or `http://` |
| `format` | `png`, `jpeg`, `webp`, `pdf` | `png` | |
| `full_page` | bool | `false` | Whole scrollable page |
| `device` | `iphone_14`, `iphone_15_pro`, `pixel_7`, `ipad_pro`, `macbook_pro` | none | Overrides width and height |
| `width` | int | `1280` | 320 to 3840 |
| `height` | int | `800` | 200 to 10000 |
| `dark_mode` | bool | `false` | Asks the page for its dark color scheme |
| `block_ads` | bool | `true` | |
| `block_cookie_banners` | bool | `true` | |
| `hide_selectors` | string | none | Comma-separated CSS selectors to hide |
| `click_selector` | string | none | Element to click before the capture |
| `delay` | int | `0` | Extra wait in ms after load, 0 to 10000 |
| `quality` | int | `90` | JPEG and WebP only |
| `include_image_data` | bool | `false` | Also return the file as a base64 data URI |
| `link_expires_in` | int | `86400` | Link lifetime in seconds, 60 to 2592000 |

Returns `screenshot_url` (a link anyone can open, ready to paste into Slack, an email or a ticket), `link_expires_at`, `format`, `width`, `height`, `size_bytes`, `served_from_cache`, `render_time` and `remaining_credits`.

Each capture uses one credit. When the same page with the same options was captured in the last 24 hours, that copy comes back for free. Opening the link serves the stored copy, so it does not use another credit while the copy is kept (24 hours on the free plan, longer on paid plans).

### ExtractContent

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `url` | string | required | |
| `content_type` | `markdown`, `text`, `html`, `article`, `links`, `metadata` | `markdown` | |
| `selector` | string | none | Read only part of the page, e.g. `main` |
| `block_ads` | bool | `true` | |
| `block_cookie_banners` | bool | `true` | |
| `delay` | int | `0` | 0 to 10000 ms |
| `max_length` | int | `100000` | 1 to 500000 characters |

Returns `url`, `type`, `content`, `word_count` and `processing_time_ms`.

### GetUsage

No parameters. Returns `plan`, `period_start`, `period_end`, `used`, `limit` and `remaining`. Free to call.

## Limits

SnapRender only captures public pages. Pages behind a login, `localhost` and private network addresses are refused. If a site you own shows a security check instead of the page, see [allowing SnapRender through your firewall](https://snap-render.com/docs/allow-snaprender).

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q
ruff check . && mypy
```

The tests mock the SnapRender API, so they need no key.

## Links

- SnapRender docs: https://snap-render.com/docs
- API reference (OpenAPI): https://app.snap-render.com/openapi.json
- Pricing: https://snap-render.com/pricing
- Support: support@snap-render.com

## License

MIT
