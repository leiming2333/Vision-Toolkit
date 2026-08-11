---
name: "text-to-image"
description: "Generate images from text prompts via OpenAI DALL-E / 通义万相 / Google Imagen. Invoke when the user asks to create, draw, generate, or make an image, illustration, or picture from a description."
---

# Text to Image

Generate an image from a natural-language prompt by calling the standalone `generate_image.py` script in this project. This skill is available to **any agent** and does **not** require the MCP server to be running — it calls the providers directly.

## Relationship with the MCP `generate_image` tool

This project exposes image generation through **two entry points** that share the same `providers/` code and the same environment-variable configuration (API keys / endpoints / models):

1. **MCP `generate_image` tool** (preferred) — available when the MCP server is connected. Use it first.
2. **This Skill** (fallback) — a standalone script. Use it when:
   - the MCP server is **not** connected / not running,
   - the MCP `generate_image` tool call **fails or times out**,
   - or you are in a context where only a Skill works (CI, batch, an agent without MCP).

**Configuration source**: the Skill reads the same environment variables as the MCP server (`OPENAI_API_KEY` / `DASHSCOPE_API_KEY` / `GEMINI_API_KEY` and the corresponding `*_BASE_URL` / `*_IMAGE_MODEL`). By default the Skill shares the MCP config — whatever the MCP server uses, the Skill uses too.

**Skill-independent config (optional)**: the Skill also supports a separate config layer via `SKILL_*`-prefixed env vars. At runtime the Skill reads `SKILL_<name>` first; if unset it falls back to `<name>`. The MCP server does **not** read `SKILL_*` vars, so MCP behavior is unaffected. Set `SKILL_*` vars only when you want the Skill to use a different key / endpoint / model than MCP — e.g. `SKILL_OPENAI_API_KEY`, `SKILL_OPENAI_BASE_URL`, `SKILL_DASHSCOPE_API_KEY`, `SKILL_GEMINI_API_KEY`. If neither `SKILL_*` nor the shared key is set, tell the user to set the relevant environment variable.

> The Skill script also has built-in **provider auto-fallback**: if the chosen provider fails, it automatically retries the other configured providers. So prefer the MCP tool first; if it fails, run this Skill script and it will try every available provider.

## When to invoke

Invoke this skill when the user wants to **create / draw / generate / make** an image, illustration, picture, or visual from a text description.

Do **not** invoke for: analyzing an existing image, OCR, object detection, or image comparison — those use the MCP tools (`analyze_image`, `ocr`, `detect_objects`, `compare_images`) instead.

## How it works

The script `scripts/generate_image.py` reads provider API keys from environment variables and calls the chosen provider's text-to-image API:

- `openai`  → DALL·E 3 (env: `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, `OPENAI_IMAGE_MODEL`)
- `qwen`    → 通义万相 wanx2.1 (env: `DASHSCOPE_API_KEY`, `QWEN_IMAGE_MODEL`)
- `gemini`  → Google Imagen 3 (env: `GEMINI_API_KEY`, `GEMINI_IMAGE_MODEL`)

## Usage

Run the script with Python. It returns either a saved PNG file path (default) or a data URL.

### Save to a file (default)

```bash
python scripts/generate_image.py --prompt "赛博朋克风格的猫咪" --provider qwen --out cat.png
# → prints absolute path to cat.png
```

### Print a data URL only

```bash
python scripts/generate_image.py --prompt "a cat" --provider openai --data-url
# → prints data:image/png;base64,...
```

### Arguments

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--prompt` / `-p` | yes | — | Image description |
| `--provider` | no | `openai` | `openai` / `qwen` / `gemini` |
| `--size` | no | `1024x1024` | Image size |
| `--out` / `-o` | no | `generated.png` | Output file path |
| `--data-url` | no | false | Print data URL instead of saving a file |

## Workflow for the agent

1. **Prefer the MCP tool first.** If the MCP server is connected, call the `generate_image` MCP tool (it also auto-falls back across providers). Only proceed to this Skill script if the MCP tool is unavailable, fails, or times out.
2. Confirm or refine the user's prompt (translate to a vivid description if needed).
3. Pick a provider:
   - If the user names one (e.g. "用通义生图"), use it.
   - Otherwise prefer `qwen` for Chinese prompts, `openai` for English, `gemini` as fallback. Only choose a provider whose API key is set in the environment.
4. Decide the output: save to a file (default) unless the user wants inline/embedded output, in which case use `--data-url`.
5. Run the script via `RunCommand` (Python). The script auto-tries other configured providers if the first one fails. If it fails with "未配置任何 provider" or "所有 provider 生图均失败", tell the user which API key to set and stop.
6. After success:
   - If a file was saved, report its absolute path and offer to open it.
   - If a data URL was returned, embed or use it as the user intended.

## Environment variables

At least one provider key must be set. The script reuses the same keys as the MCP server:

```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1     # optional, OpenAI-compatible endpoints
OPENAI_IMAGE_MODEL=dall-e-3

DASHSCOPE_API_KEY=sk-...
QWEN_IMAGE_MODEL=wanx2.1-t2i-turbo

GEMINI_API_KEY=...
GEMINI_IMAGE_MODEL=imagen-3.0-generate-002
```

### Skill-independent config (optional)

To give the Skill a **different** key / endpoint / model than MCP, set `SKILL_*`-prefixed vars. The Skill reads `SKILL_<name>` first, falling back to `<name>`:

```
SKILL_OPENAI_API_KEY=sk-skill-...             # Skill 用单独的 OpenAI Key
SKILL_OPENAI_BASE_URL=https://my-proxy/v1      # Skill 用单独的端点
SKILL_OPENAI_IMAGE_MODEL=dall-e-3
SKILL_DASHSCOPE_API_KEY=sk-skill-qwen-...
SKILL_QWEN_IMAGE_MODEL=wanx2.1-t2i-turbo
SKILL_GEMINI_API_KEY=...
```

MCP server does not read `SKILL_*` vars, so its behavior is unaffected.

## Notes

- The script is standalone and shares `providers/` with the MCP server, so all three providers are supported with no extra setup.
- For Qwen, the `--size` separator is auto-converted from `1024x1024` to `1024*1024`.
- The script must be run from the project root so it can import `providers/`. If run elsewhere, use an absolute path and ensure `providers/` is importable.
