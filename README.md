# Vision Toolkit

> Multimodal vision **MCP Server** + standalone **Text-to-Image Skill**.
>
> Integrates **OpenAI GPT-4o · Tongyi Qwen-VL · Google Gemini**:
> - **MCP tools**: image description/QA, OCR, object detection, text-to-image, image similarity
> - **Standalone Skill**: generate images directly, available to any agent, no MCP server required

**English** | [中文](README.zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)
[![Skill](https://img.shields.io/badge/TRAE-Skill-green.svg)](https://.)
[![npm](https://img.shields.io/badge/npm-vision--toolkit-red.svg)](https://www.npmjs.com/package/vision-toolkit)

---

## Table of Contents

- [Features](#features)
- [Capability Matrix](#capability-matrix)
- [Installation](#installation)
- [Quick Start](#quick-start)
  - [Option 1: Start the MCP server (stdio, recommended for MCP clients)](#option-1-start-the-mcp-server-stdio-recommended-for-mcp-clients)
  - [Option 2: SSE remote mode](#option-2-sse-remote-mode)
  - [Option 3: Standalone Skills (no MCP server, works for any agent)](#option-3-standalone-skills-no-mcp-server-works-for-any-agent)
- [Configure Provider Keys](#configure-provider-keys)
- [Connect to MCP Clients](#connect-to-mcp-clients)
  - [Trae (native Skills + MCP)](#trae-native-skills--mcp)
  - [Clients using the `mcpServers` JSON format](#clients-using-the-mcpservers-json-format)
  - [Claude Code](#claude-code)
  - [OpenCode](#opencode)
  - [Codex CLI (OpenAI)](#codex-cli-openai)
  - [Continue](#continue)
  - [Gemini CLI](#gemini-cli)
  - [Zed](#zed)
  - [SSE remote mode](#sse-remote-mode)
- [MCP Tools](#mcp-tools)
- [Text-to-Image Skill](#text-to-image-skill)
  - [Generation fallback strategy](#generation-fallback-strategy)
  - [When to use](#when-to-use)
  - [Call the script directly](#call-the-script-directly)
  - [Script arguments](#script-arguments)
- [Image Analysis Skill](#image-analysis-skill)
  - [Analysis fallback strategy](#analysis-fallback-strategy)
  - [When to use](#when-to-use-1)
  - [Call the script directly](#call-the-script-directly-1)
  - [Subcommands & arguments](#subcommands--arguments)
- [CLI Options](#cli-options)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [FAQ](#faq)
- [Development](#development)
- [License](#license)

---

## Features

- **MCP + Skill, two entry points**: The MCP server offers 6 tools (vision/generation/comparison); two standalone Skills let any agent generate images and analyze images without connecting to MCP.
- **Multi-model aggregation**: Auto-loads providers based on available API keys at startup; switch via the `provider` parameter.
- **6 ready-to-use MCP tools**: image description/QA, OCR, object detection, text-to-image, image similarity, provider list.
- **Text-to-Image Skill**: Decoupled from the MCP protocol — any agent can generate images via `scripts/generate_image.py` as long as an API key is set.
- **Image Analysis Skill**: Any agent can describe/OCR/detect/compare images via `scripts/vision.py`, no MCP server needed.
- **Unified image input**: local path / HTTP(S) URL / data URL are all auto-normalized.
- **Dual transport (MCP)**: stdio (default for local clients) and SSE (remote/debug).
- **One-line npm install**: Run via `npx` / `npm i -g`; Python deps are auto-managed.
- **Pluggable providers**: Add a new vision model by subclassing `VisionProvider` and registering it.

## Capability Matrix

| Provider | Vision analysis | Text-to-image | Image embedding |
|----------|:---------------:|:-------------:|:---------------:|
| **OpenAI** GPT-4o + DALL·E 3 | ✅ | ✅ | ⚠️ describe-fallback |
| **Tongyi Qwen** Qwen-VL + Wanxiang | ✅ | ✅ | ✅ native multimodal |
| **Google** Gemini + Imagen 3 | ✅ | ✅ | ⚠️ describe-fallback |

> OpenAI / Gemini have no public image embedding API, so a "describe-then-text-embed" fallback is used. Tongyi Qwen `multimodal-embedding-one-peace-v1` is a native multimodal image embedding.

---

## Installation

Vision Toolkit offers two install methods. **Prerequisite**: Python 3.10+ and at least one provider API key.

> **Looking to connect an AI agent?** Most MCP-compatible clients (Trae, Claude Desktop, Cursor, Windsurf, Cline, Continue, Roo Code, OpenCode, Codex CLI, Gemini CLI, Zed, GitHub Copilot, Claude Code) can launch Vision Toolkit automatically via `npx vision-toolkit`. Skip to [Connect to MCP Clients](#connect-to-mcp-clients) for per-client config snippets.

### Method A: Install via npm (recommended, Python deps auto-managed)

```bash
# 1. Run on-the-fly without installing — the typical entry point used by MCP clients
npx vision-toolkit

# 2. Install globally (then the `vision-toolkit` command is on PATH)
npm install -g vision-toolkit
vision-toolkit

# 3. Install into your project
npm install vision-toolkit
npx vision-toolkit
```

On first run, the Node wrapper auto-detects Python and tries to install dependencies (`mcp`, `httpx`, etc.). If auto-install fails, run manually:

```bash
npm run setup
# or
vision-toolkit --setup
```

Installing from GitHub is also supported:

```bash
npm install -g github:leiming2333/Vision-Toolkit
```

### Method B: Local install (clone + pip)

Clone the source and install Python deps manually. After this you can run the MCP server **and** use the standalone Skills directly.

```bash
git clone https://github.com/leiming2333/Vision-Toolkit.git
cd Vision-Toolkit
pip install -r requirements.txt

# Start the MCP server
python server.py
# Or use the standalone Skills directly (no MCP needed):
python scripts/generate_image.py --prompt "a cat" --provider qwen --out cat.png
python scripts/vision.py analyze --image cat.jpg
```

> After installation, see [Configure Provider Keys](#configure-provider-keys) to set up API keys.

---

## Quick Start

After installation (see [Installation](#installation)), start using Vision Toolkit as follows.

### Option 1: Start the MCP server (stdio, recommended for MCP clients)

```bash
# Installed via npm
vision-toolkit
# or run on-the-fly
npx vision-toolkit

# Or installed via manual clone
python server.py
```

Once started, connect from your MCP client (Trae / Claude Desktop). See [Connect to MCP Clients](#connect-to-mcp-clients).

### Option 2: SSE remote mode

```bash
vision-toolkit --transport sse --host 0.0.0.0 --port 8765
```

### Option 3: Standalone Skills (no MCP server, works for any agent)

No MCP server needed — any agent can call the scripts directly once the API key is set:

```bash
# Text-to-Image Skill
python scripts/generate_image.py --prompt "a cyberpunk cat" --provider qwen --out cat.png
# prints the absolute path of cat.png

# Image Analysis Skill
python scripts/vision.py analyze --image cat.jpg --prompt "What's in this image?"
```

The Skills are auto-detected by TRAE and triggered when the user says "draw / generate / make an image" or "describe / OCR / detect / compare an image".

---

## Configure Provider Keys

Configure at least **one** provider API key to start. Multiple keys allow switching.

### Interactive wizard (recommended)

Run the built-in configuration wizard — it guides you through provider selection, API key, base URL, and model ID (MODID). Settings are saved to `~/.vision-toolkit.env` and auto-loaded on server start.

```bash
vision-toolkit --configure
```

The wizard covers:
- **Provider**: OpenAI / Qwen / Gemini / Anthropic Claude / custom OpenAI-compatible endpoint
- **API Key**: required for the selected provider
- **Base URL**: for OpenAI-compatible endpoints (proxy / self-hosted supported)
- **Model ID (MODID)**: optional — if skipped, the server auto-detects available models via `GET {base_url}/models` on startup

### Manual configuration

Alternatively, copy [.env.example](.env.example) to `.env`, or set system environment variables directly:

```bash
# Windows
set OPENAI_API_KEY=sk-...
set DASHSCOPE_API_KEY=sk-...
set GEMINI_API_KEY=...

# macOS / Linux
export OPENAI_API_KEY=sk-...
export DASHSCOPE_API_KEY=sk-...
export GEMINI_API_KEY=...
```

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI key | — |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint (proxy supported) | `https://api.openai.com/v1` |
| `OPENAI_VISION_MODEL` | Vision model | `gpt-4o` |
| `OPENAI_IMAGE_MODEL` | Image generation model | `dall-e-3` |
| `OPENAI_EMBEDDING_MODEL` | Text embedding model (for image similarity) | `text-embedding-3-small` |
| `DASHSCOPE_API_KEY` | Alibaba DashScope key | — |
| `QWEN_VL_MODEL` | Qwen vision model | `qwen-vl-plus` |
| `QWEN_IMAGE_MODEL` | Wanxiang image model | `wanx2.1-t2i-turbo` |
| `QWEN_EMBEDDING_MODEL` | Multimodal embedding model | `multimodal-embedding-one-peace-v1` |
| `GEMINI_API_KEY` | Google AI key | — |
| `GEMINI_VISION_MODEL` | Gemini vision model | `gemini-2.0-flash` |
| `GEMINI_IMAGE_MODEL` | Imagen image model | `imagen-3.0-generate-002` |
| `GEMINI_EMBEDDING_MODEL` | Text embedding model (for image similarity) | `text-embedding-004` |
| `ANTHROPIC_API_KEY` | Anthropic (Claude) key | — |
| `ANTHROPIC_BASE_URL` | Anthropic API endpoint | `https://api.anthropic.com` |
| `ANTHROPIC_VISION_MODEL` | Claude vision model (analysis only, no generation/embedding) | `claude-sonnet-4-20250514` |
| `ANTHROPIC_API_VERSION` | Anthropic API version header | `2023-06-01` |

### Skill-independent config (optional)

By default the Skill scripts share the same env vars as the MCP server above — zero extra setup. If you want the Skills to use a **different** key / endpoint / model than MCP, set `SKILL_*`-prefixed vars. At runtime the Skill reads `SKILL_<name>` first, falling back to `<name>`; the MCP server does **not** read `SKILL_*` vars, so its behavior is unaffected.

```bash
# Example: Skills use a separate OpenAI-compatible endpoint and key
SKILL_OPENAI_API_KEY=sk-skill-...
SKILL_OPENAI_BASE_URL=https://my-proxy.example.com/v1
SKILL_OPENAI_IMAGE_MODEL=dall-e-3
SKILL_OPENAI_VISION_MODEL=gpt-4o

# Example: Skills use a separate Tongyi / Gemini key
SKILL_DASHSCOPE_API_KEY=sk-skill-qwen-...
SKILL_GEMINI_API_KEY=...
```

Any variable above can be prefixed with `SKILL_` to override it for the Skills only (e.g. `SKILL_QWEN_IMAGE_MODEL`, `SKILL_GEMINI_VISION_MODEL`, `SKILL_OPENAI_EMBEDDING_MODEL`). Unset `SKILL_*` vars simply fall back to the shared value.

---

## Connect to MCP Clients

Vision Toolkit follows the standard MCP protocol, so any MCP-compatible client can connect. The snippets below cover the most popular agents in 2026. All examples assume you set API keys via `env` (or your shell); see [Configure Provider Keys](#configure-provider-keys).

### Trae (native Skills + MCP)

Vision Toolkit ships with two TRAE-native Skills (`.trae/skills/`), so Trae users get the best out-of-the-box experience: the Skills are auto-loaded by the workspace, **and** the MCP server can be connected for the full 6-tool set.

**Option A — UI (recommended):** Settings → MCP → Add → Configure Manually → paste the JSON below.

**Option B — project-level config:** create `.trae/mcp.json` in your project root (enable "Project-level MCP" in Settings → MCP first):

```json
{
  "mcpServers": {
    "vision": {
      "command": "npx",
      "args": ["-y", "vision-toolkit"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "DASHSCOPE_API_KEY": "sk-..."
      }
    }
  }
}
```

After connecting, Trae will use the MCP tools (`analyze_image`, `generate_image`, etc.) **and** auto-detect the two Skills in `.trae/skills/` for standalone image generation / analysis — no extra setup needed.

### Clients using the `mcpServers` JSON format

The following clients all share the same `mcpServers` JSON schema — copy the same block into the config file for each:

| Client | Config file location |
|--------|----------------------|
| **Trae** | Workspace / global MCP settings (UI or `mcp.json`) |
| **Claude Desktop** | macOS: `~/Library/Application Support/Claude/claude_desktop_config.json` · Windows: `%APPDATA%\Claude\claude_desktop_config.json` |
| **Cursor** | Global: `~/.cursor/mcp.json` · Project: `.cursor/mcp.json` |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` |
| **Cline** (VS Code) | `cline_mcp_settings.json` (Cline MCP panel → Configure) |
| **Roo Code** (VS Code) | Global: `mcp_settings.json` · Project: `.roo/mcp.json` |
| **GitHub Copilot** (VS Code) | `~/.vscode/mcp.json` (VS Code 1.102+) or `.vscode/mcp.json` |

```json
{
  "mcpServers": {
    "vision": {
      "command": "npx",
      "args": ["-y", "vision-toolkit"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "DASHSCOPE_API_KEY": "sk-..."
      }
    }
  }
}
```

If installed globally, use the direct binary instead:

```json
{
  "mcpServers": {
    "vision": {
      "command": "vision-toolkit",
      "env": { "GEMINI_API_KEY": "..." }
    }
  }
}
```

Manual Python (clone install):

```json
{
  "mcpServers": {
    "vision": {
      "command": "python",
      "args": ["/path/to/Vision-Toolkit/server.py"],
      "env": { "OPENAI_API_KEY": "sk-..." }
    }
  }
}
```

> Some clients (Cursor, Cline) hot-reload after editing; Claude Desktop requires a full restart.

### Claude Code

Claude Code uses `~/.claude.json` (user scope) or `.mcp.json` (project scope). The schema is the same `mcpServers` JSON as above. You can also add it via CLI:

```bash
claude mcp add vision --env OPENAI_API_KEY=sk-... --env DASHSCOPE_API_KEY=sk-... -- npx -y vision-toolkit
```

### OpenCode

OpenCode uses `opencode.json` / `opencode.jsonc` (in `~/.config/opencode/` or the project root) with a slightly different shape: `command` is an array and the key is `mcp` (not `mcpServers`).

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "vision": {
      "type": "local",
      "command": ["npx", "-y", "vision-toolkit"],
      "enabled": true,
      "environment": {
        "OPENAI_API_KEY": "sk-...",
        "DASHSCOPE_API_KEY": "sk-..."
      }
    }
  }
}
```

### Codex CLI (OpenAI)

Codex stores MCP config in `~/.codex/config.toml` using TOML. Note the snake_case key `mcp_servers` (not `mcpServers`).

```toml
[mcp_servers.vision]
command = "npx"
args = ["-y", "vision-toolkit"]
env = { OPENAI_API_KEY = "sk-...", DASHSCOPE_API_KEY = "sk-..." }
startup_timeout_sec = 20
```

Or via the CLI:

```bash
codex mcp add vision --env OPENAI_API_KEY=sk-... --env DASHSCOPE_API_KEY=sk-... -- npx -y vision-toolkit
```

Verify with `codex mcp list` or run `/mcp` inside the Codex TUI.

### Continue

Continue reads MCP servers from YAML config (`~/.continue/config.yaml` or `.continue/mcpServers/<name>.yaml` in the workspace).

```yaml
mcpServers:
  - name: vision
    type: stdio
    command: npx
    args:
      - "-y"
      - "vision-toolkit"
    env:
      OPENAI_API_KEY: sk-...
      DASHSCOPE_API_KEY: sk-...
```

### Gemini CLI

Gemini CLI reads `~/.gemini/settings.json` and accepts the standard `mcpServers` JSON shape.

```json
{
  "mcpServers": {
    "vision": {
      "command": "npx",
      "args": ["-y", "vision-toolkit"],
      "env": { "GEMINI_API_KEY": "..." }
    }
  }
}
```

### Zed

Zed stores MCP servers under `context_servers` in `~/.config/zed/settings.json` (macOS: `~/Library/Application Support/Zed/settings.json`).

```json
{
  "context_servers": {
    "vision": {
      "command": {
        "path": "npx",
        "args": ["-y", "vision-toolkit"]
      },
      "env": { "OPENAI_API_KEY": "sk-..." }
    }
  }
}
```

### SSE remote mode

Start on the server:

```bash
vision-toolkit --transport sse --host 0.0.0.0 --port 8765
```

Client config (JSON clients):

```json
{
  "mcpServers": {
    "vision": {
      "transport": {
        "type": "sse",
        "url": "http://your-server:8765/sse"
      }
    }
  }
}
```

Codex CLI (TOML) — use `url` instead of `command`:

```toml
[mcp_servers.vision]
url = "http://your-server:8765/sse"
```

OpenCode (JSON):

```json
{
  "mcp": {
    "vision": {
      "type": "remote",
      "url": "http://your-server:8765/sse",
      "enabled": true
    }
  }
}
```

---

## MCP Tools

| Tool | Description | Key params |
|------|-------------|------------|
| `list_providers` | List configured providers and capabilities | — |
| `analyze_image` | Image description / visual QA | `image`, `prompt`, `provider?` |
| `ocr` | Extract text from image | `image`, `language?`, `provider?` |
| `detect_objects` | Object detection (label + confidence + 9-grid position) | `image`, `provider?` |
| `generate_image` | Text-to-image, returns data URL | `prompt`, `size?`, `provider?` |
| `compare_images` | Image similarity (cosine, 0~1) | `image1`, `image2`, `provider?` |

All `image` params accept: **local path** / **HTTP(S) URL** / **data URL**.

`provider` can be `openai` / `qwen` / `gemini`; omit to use the default (first configured provider).

### Examples

```
Tool: analyze_image
Args: { "image": "https://example.com/cat.jpg", "prompt": "How many cats?" }

Tool: generate_image
Args: { "prompt": "a cyberpunk cat", "size": "1024x1024", "provider": "qwen" }

Tool: compare_images
Args: { "image1": "./a.png", "image2": "https://example.com/b.png" }
```

---

## Text-to-Image Skill

The project ships with a TRAE **Skill** (`.trae/skills/text-to-image/`) that lets **any agent** generate images directly, without starting the MCP server.

It calls the same `providers/` code, so behavior and supported providers are identical to the MCP `generate_image` tool.

### Generation fallback strategy

Vision Toolkit uses a layered fallback for image generation. **By default the MCP tool is used; the Skill script only kicks in when the MCP path is unavailable or fails.**

1. **MCP `generate_image` tool first** — when the MCP server is connected, the AI calls this tool. The tool itself also auto-falls back across configured providers (e.g. `openai` → `qwen` → `gemini`): if the chosen provider errors, it retries the next configured one until one succeeds or all fail.
2. **Skill script as fallback** — only when the MCP tool is unavailable, fails, or times out does the AI run `scripts/generate_image.py`. The script also auto-tries other configured providers if the chosen one fails.

**Shared configuration (single source of truth)**: the MCP tool and the Skill script read the **same** environment variables — `OPENAI_API_KEY` / `DASHSCOPE_API_KEY` / `GEMINI_API_KEY` and the corresponding `*_BASE_URL` / `*_IMAGE_MODEL`. There is no separate Skill config; whatever the MCP server uses, the Skill uses too. If a key configured for MCP is missing or unusable, the Skill cannot conjure a replacement — in that case tell the user to set the relevant environment variable.

### When to use

| Scenario | Use which? |
|----------|-----------|
| Inside an MCP client already connected to this project | Prefer the `generate_image` MCP tool |
| No MCP connection, or want any agent / automation script to use it | **Text-to-Image Skill** / standalone script |

**Trigger words**: generate, draw, paint, make/create an image/picture/illustration.

### Call the script directly

Script path: [scripts/generate_image.py](scripts/generate_image.py)

```bash
# Save to a local PNG (default), prints absolute path
python scripts/generate_image.py --prompt "a cyberpunk cat" --provider qwen --out cat.png

# English prompt → openai recommended; Chinese → qwen; gemini as fallback
python scripts/generate_image.py --prompt "a cozy mountain cabin at sunset" --provider openai

# Custom size
python scripts/generate_image.py --prompt "a cat" --size 1024x1792 --provider openai

# Print data URL only (no file saved)
python scripts/generate_image.py --prompt "a cat" --provider qwen --data-url
```

### Script arguments

| Flag | Short | Required | Default | Description |
|------|-------|----------|---------|-------------|
| `--prompt` | `-p` | ✅ | — | Image description |
| `--provider` | | no | `openai` | `openai` / `qwen` / `gemini` (must have API key set) |
| `--size` | | no | `1024x1024` | Image size; Qwen auto-converts `x` to `*` |
| `--out` | `-o` | no | `generated.png` | Output filename; `.png` appended automatically |
| `--data-url` | | no | false | Print `data:image/png;base64,...` instead of saving a file |

### Agent workflow (built into SKILL.md)

The Skill defines a standard procedure the AI follows:

1. Confirm/refine the prompt.
2. Pick a provider: user-specified first; otherwise Chinese → qwen, English → openai, gemini fallback; only pick one with a key set.
3. Output form: save to file by default; use `--data-url` only when the user wants inline/embedded output.
4. Call the Python script via `RunCommand`; if it reports "no provider configured", tell the user to set an API key.
5. Report the file path or data URL to the user.

### Skill file location

```
vision-toolkit/.trae/skills/text-to-image/
└── SKILL.md   # TRAE-native Skill definition
```

After cloning the project and opening it in TRAE, the Skill is auto-loaded by the workspace.

---

## Image Analysis Skill

The project also ships with a TRAE **Skill** (`.trae/skills/image-analysis/`) that lets **any agent** understand an **existing** image directly, without starting the MCP server. It supports four operations: image description/QA, OCR, object detection, and image similarity comparison.

It calls the same `providers/` code, so behavior and supported providers are identical to the MCP `analyze_image` / `ocr` / `detect_objects` / `compare_images` tools.

### Analysis fallback strategy

Vision Toolkit uses a layered fallback for image understanding. **By default the MCP tools are used; the Skill script only kicks in when the MCP path is unavailable or fails.**

1. **MCP tools first** — when the MCP server is connected, the AI calls `analyze_image` / `ocr` / `detect_objects` / `compare_images`. The Skill script is not needed.
2. **Skill script as fallback** — only when an MCP tool is unavailable, fails, or times out does the AI run `scripts/vision.py`. The script also auto-falls back across configured providers: if the chosen provider errors, it retries the next configured one until one succeeds or all fail. For `compare`, native multimodal-embedding providers (Tongyi Qwen) are preferred; OpenAI/Gemini fall back to a "describe-then-text-embed" strategy.

**Shared configuration (single source of truth)**: the MCP tools and the Skill script read the **same** environment variables — `OPENAI_API_KEY` / `DASHSCOPE_API_KEY` / `GEMINI_API_KEY` and the corresponding `*_BASE_URL` / `*_VISION_MODEL`. There is no separate Skill config; whatever the MCP server uses, the Skill uses too.

### When to use

| Scenario | Use which? |
|----------|-----------|
| Inside an MCP client already connected to this project | Prefer the MCP tools (`analyze_image` / `ocr` / `detect_objects` / `compare_images`) |
| No MCP connection, or want any agent / automation script to use it | **Image Analysis Skill** / standalone script |

**Trigger words**: describe, analyze, understand, read text from, OCR, detect objects in, compare images.

### Call the script directly

Script path: [scripts/vision.py](scripts/vision.py)

```bash
# Describe an image (default prompt)
python scripts/vision.py analyze --image cat.jpg

# Visual QA
python scripts/vision.py analyze --image cat.jpg --prompt "How many cats?"

# OCR (extract text), optional language hint
python scripts/vision.py ocr --image doc.png --language zh

# Object detection (label + confidence + 9-grid position)
python scripts/vision.py detect --image street.jpg

# Image similarity (cosine, 0~1)
python scripts/vision.py compare --image1 a.png --image2 b.png
```

### Subcommands & arguments

All `image` / `image1` / `image2` args accept: **local path** / **HTTP(S) URL** / **data URL**.

`--provider` is optional for every subcommand (`openai` / `qwen` / `gemini`); omit to use the default. If the chosen provider fails, the script auto-tries the others.

| Subcommand | Args | Description |
|-----------|------|-------------|
| `analyze` | `--image` (req), `--prompt?`, `--provider?` | Image description / visual QA |
| `ocr` | `--image` (req), `--language?`, `--provider?` | Extract text, preserve line breaks |
| `detect` | `--image` (req), `--provider?` | Object detection (label + confidence + 9-grid position) |
| `compare` | `--image1` (req), `--image2` (req), `--provider?` | Image similarity (cosine 0~1) |

### Skill file location

```
vision-toolkit/.trae/skills/image-analysis/
└── SKILL.md   # TRAE-native Skill definition
```

After cloning the project and opening it in TRAE, the Skill is auto-loaded by the workspace.

---

## CLI Options

```bash
vision-toolkit [options]

Options:
  --transport <stdio|sse>   Transport mode, default stdio
  --host <addr>             SSE listen address, default 127.0.0.1
  --port <n>                SSE listen port, default 8765
  --python <path>           Specify Python interpreter path
  --setup                   Install Python deps and exit
  --configure               Interactive config wizard (API key / URL / model, saved to ~/.vision-toolkit.env)
  -p <path>                 Shortcut for --python
```

You can also set the Python interpreter via the `VISION_TOOLKIT_PYTHON` environment variable.

---

## Project Structure

```
vision-toolkit/
├── package.json                 # npm package definition (bin / scripts / postinstall / files)
├── bin/
│   ├── cli.js                   # Node.js entry, spawns Python server.py
│   └── postinstall.js           # npm install hook, auto-installs Python deps (non-blocking)
├── server.py                    # Main MCP service + 6 tools (vision/generation/comparison)
├── image_utils.py               # Image input normalization (path/URL/data URL)
├── providers/
│   ├── __init__.py              # Provider registry
│   ├── base.py                  # Abstract base VisionProvider (analyze / generate / embed)
│   ├── openai_provider.py       # OpenAI: GPT-4o + DALL·E 3 + text embedding
│   ├── qwen_provider.py         # Tongyi Qwen: Qwen-VL + Wanxiang + multimodal embedding
│   └── gemini_provider.py       # Gemini + Imagen 3 + text embedding
├── scripts/
│   ├── generate_image.py        # Standalone text-to-image CLI (called by the text-to-image Skill)
│   └── vision.py                # Standalone vision CLI (called by the image-analysis Skill)
├── .trae/
│   └── skills/
│       ├── text-to-image/
│       │   └── SKILL.md         # TRAE Skill: when/how to generate an image
│       └── image-analysis/
│           └── SKILL.md         # TRAE Skill: when/how to analyze/OCR/detect/compare
├── requirements.txt             # Python deps (shared by MCP + Skill)
├── .env.example                 # Environment variable template
├── .gitignore                   # Avoid committing caches, .env, etc.
├── .npmignore                   # Files excluded when publishing to npm
├── LICENSE                      # MIT
├── README.md                    # English documentation (default)
└── README.zh.md                 # Chinese documentation
```

---

## How It Works

```
  Entry A: MCP client                  Entry B: Any agent / script
 (Trae / Claude Desktop)                  (TRAE Skill / CI / manual)
          │                                          │
          │ stdio / SSE                              │ RunCommand
          ▼                                          ▼
  ┌───────────────────┐                  ┌──────────────────────────┐
  │  server.py        │                  │ scripts/generate_image.py│  (text→image)
  │  (MCP SDK, 6 tools)│                  │ scripts/vision.py        │  (image analysis)
  └─────────┬─────────┘                  └────────────┬─────────────┘
            │                                       │
            └─────────────── shared providers ──────┘
                                  │
                                  ▼
                   ┌───────────────────────────┐
                   │ Vision/image model HTTP:  │
                   │ OpenAI / Qwen / Gemini /  │
                   │ Anthropic Claude          │
                   └───────────────────────────┘

  npm entry wrapper (pick one):
  └─────────────────────────────────────────────────┐
    npx vision-toolkit  ──► bin/cli.js ──► server.py
    (CLI args, Python detection, auto pip install)
  └─────────────────────────────────────────────────┘
```

### Entry A — MCP Server (vision + generation + comparison)

1. User runs `npx vision-toolkit` (or has `mcpServers` configured in the client); the Node wrapper `bin/cli.js` starts.
2. The wrapper detects an available Python interpreter and runs `pip install` if needed.
3. The wrapper `spawn`s Python to run `server.py`, forwarding all args and stdio.
4. `server.py` registers 6 tools via the official `mcp` SDK and loads providers based on API keys.
5. The MCP client calls tools via stdio/SSE; the server forwards to the corresponding vision model API.

### Entry B — Standalone Skills (any agent, no MCP needed)

Two Skills ship with the project, each backed by a standalone script:

- **Text-to-Image Skill** → `scripts/generate_image.py` (generate an image from text)
- **Image Analysis Skill** → `scripts/vision.py` (describe / OCR / detect / compare an existing image)

1. The user says "generate/draw an image..." or "describe/OCR/detect/compare this image..."; TRAE detects the matching `.trae/skills/*/SKILL.md` and activates the Skill.
2. The AI picks a provider and operation per the Skill workflow.
3. The AI calls the script directly via `RunCommand`.
4. The script reads API keys from env vars and reuses the implementations in `providers/`, auto-falling back across configured providers on failure.
5. The script prints the result (file path / data URL / text / similarity score); the AI reports it to the user.

> All entries share the same `providers/` code and API keys, so behavior and supported models are identical. The only difference: Entry A exposes all capabilities **through the MCP protocol**; Entry B is a lightweight script **decoupled from MCP**, for generation **and** analysis.

---

## FAQ

**Q: Python dependency install failed during `npm install`?**
A: postinstall failure does not block installation. Run `npm run setup` or `vision-toolkit --setup` manually; it also auto-retries on first run.

**Q: What happens if no API key is configured?**
A: The server starts but has no provider; tool calls return a hint. Use the `list_providers` tool to check available providers.

**Q: How do I use a third-party OpenAI-compatible endpoint?**
A: Set `OPENAI_BASE_URL` to that endpoint (proxy, Azure, local vLLM, etc.).

**Q: How accurate is image similarity?**
A: Tongyi Qwen's native multimodal embedding is closest to image content; OpenAI/Gemini use a describe-fallback, leaning toward semantic similarity.

**Q: Are locally deployed models supported?**
A: Yes. Point `OPENAI_BASE_URL` to a local OpenAI-compatible endpoint (vLLM, Ollama's OpenAI API, etc.).

**Q: Why two text-to-image paths (MCP tool vs Skill script)?**
A: Different scenarios:
- **MCP `generate_image` tool**: Inside an MCP-connected client, the AI auto-uses all capabilities (vision/generation/comparison); generation is just one part.
- **Text-to-Image Skill**: No MCP connection needed, any agent can use it; ideal for standalone generation, CI, batch scripts, or when Trae has no MCP configured.

Both call the same code and produce identical results. The same applies to image analysis: MCP `analyze_image` / `ocr` / `detect_objects` / `compare_images` tools vs the **Image Analysis Skill** (`scripts/vision.py`).

**Q: The Text-to-Image Skill isn't working in TRAE?**
A: Check:
1. The workspace root contains `.trae/skills/text-to-image/SKILL.md` (TRAE opened `vision-toolkit/` or a parent dir).
2. Use clear trigger words: "generate an image of...", "draw a...", "make a picture", "create an image".
3. `scripts/generate_image.py` runs successfully manually (rule out key/dependency issues first).

**Q: The Image Analysis Skill isn't working in TRAE?**
A: Same checks as above, but for `.trae/skills/image-analysis/SKILL.md` and `scripts/vision.py`. Trigger words: "describe/analyze this image", "read the text in this image / OCR", "detect objects in this image", "compare these two images".

**Q: Can I use only the Skill without MCP, or only MCP without the Skill?**
A: Yes. The entry points are independent:
- Only generate images → use only the Text-to-Image Skill, no need to start the MCP server.
- Only analyze images → use only the Image Analysis Skill, no need to start the MCP server.
- Only use MCP → all 6 tools (vision/generation/comparison) are available; the Skills are optional fallbacks.
- Need both → use both; the AI picks the right entry based on context.

---

## Development

### Add a new Provider

1. Create `xxx_provider.py` under `providers/`, subclass `VisionProvider` and implement `analyze` / `generate` (/ `embed`).
2. Register it in `PROVIDER_CLASSES` in [providers/__init__.py](providers/__init__.py).
3. Done. Tools can now switch via `provider="xxx"`.

### Local debugging

```bash
# Install deps
pip install -r requirements.txt

# 1) MCP stdio mode (use with MCP Inspector)
npx @modelcontextprotocol/inspector python server.py

# 2) MCP SSE mode
python server.py --transport sse --port 8765

# 3) Skill / standalone generation script (no MCP needed)
python scripts/generate_image.py --prompt "a test cat" --provider qwen --out test.png
```

### Publish to npm

```bash
npm version patch
npm publish
```

> Before publishing, update `homepage` / `repository.url` / `author` in `package.json` to your own.

---

## License

[MIT](LICENSE)
