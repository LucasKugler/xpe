# OpenCode V2 integration

Registers the xpe/xte/xve command-line tools as native OpenCode V2 plugin tools:

| Tool | Command |
| --- | --- |
| `xml_query` | `xpe` |
| `xml_transform` | `xte` |
| `xml_validate` | `xve` |

## Install

Copy the plugin directory into the OpenCode config directory:

```bash
cp -r plugins/xml ~/.config/opencode/plugins/
```

OpenCode discovers `~/.config/opencode/plugins/xml/` automatically, so no
`plugins` entry in `opencode.jsonc` is needed. The OpenCode runtime provides
`@opencode/plugin`; `package.json` records a compatible version for local
type-checking and bundling.

## Layout

- `plugins/xml/index.ts` — the plugin implementation
- `package.json` — the plugin SDK version used for type-checking

The legacy V1 implementation lives in `../opencode/xml.ts` and is kept for
OpenCode V1 users.
