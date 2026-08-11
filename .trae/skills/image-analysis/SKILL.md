---
name: "image-analysis"
description: "Analyze an existing image: describe / answer questions, OCR (extract text), object detection, or compare two images for similarity. Invoke when the user asks to understand, describe, read text from, detect objects in, or compare images they already have (not generate new ones)."
---

# Image Analysis

Understand an **existing** image by calling the standalone `vision.py` script in this project. Supports four operations: image description / visual QA, OCR (text extraction), object detection, and image similarity comparison. This skill is available to **any agent** and does **not** require the MCP server to be running — it calls the providers directly.

## Relationship with the MCP vision tools

This project exposes image understanding through **two entry points** that share the same `providers/` code and the same environment-variable configuration (API keys / endpoints / models):

1. **MCP tools** (preferred) — `analyze_image`, `ocr`, `detect_objects`, `compare_images`. Available when the MCP server is connected. Use them first.
2. **This Skill** (fallback) — a standalone script. Use it when:
   - the MCP server is **not** connected / not running,
   - the MCP tool call **fails or times out**,
   - or you are in a context where only a Skill works (CI, batch, an agent without MCP).

**Configuration source**: the Skill reads the same environment variables as the MCP server (`OPENAI_API_KEY` / `DASHSCOPE_API_KEY` / `GEMINI_API_KEY` and the corresponding `*_BASE_URL` / `*_VISION_MODEL`). By default the Skill shares the MCP config — whatever the MCP server uses, the Skill uses too.

**Skill-independent config (optional)**: the Skill also supports a separate config layer via `SKILL_*`-prefixed env vars. At runtime the Skill reads `SKILL_<name>` first; if unset it falls back to `<name>`. The MCP server does **not** read `SKILL_*` vars, so MCP behavior is unaffected. Set `SKILL_*` vars only when you want the Skill to use a different key / endpoint / model than MCP — e.g. `SKILL_OPENAI_API_KEY`, `SKILL_OPENAI_BASE_URL`, `SKILL_OPENAI_VISION_MODEL`, `SKILL_DASHSCOPE_API_KEY`, `SKILL_QWEN_VL_MODEL`, `SKILL_GEMINI_API_KEY`, `SKILL_GEMINI_VISION_MODEL`. If neither `SKILL_*` nor the shared key is set, tell the user to set the relevant environment variable.

> The Skill script also has built-in **provider auto-fallback**: if the chosen provider fails, it automatically retries the other configured providers. So prefer the MCP tools first; if they fail, run this Skill script and it will try every available provider.

## When to invoke

Invoke this skill when the user wants to **understand / analyze / read from / detect in / compare** an image they already have.

Do **not** invoke for: generating a new image from text — that uses the `text-to-image` Skill / MCP `generate_image` tool instead.

Map the user's intent to a subcommand:

| User intent | Subcommand |
|-------------|-----------|
| Describe an image, answer a question about it, visual QA | `analyze` |
| Extract / read text from an image (OCR) | `ocr` |
| Detect objects, list what's in an image with positions | `detect` |
| Compare two images, check how similar they are | `compare` |

## How it works

The script `scripts/vision.py` reads provider API keys from environment variables and calls the chosen provider's vision API:

- `openai`  → GPT-4o (env: `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, `OPENAI_VISION_MODEL`)
- `qwen`    → Qwen-VL (env: `DASHSCOPE_API_KEY`, `QWEN_VL_MODEL`)
- `gemini`  → Gemini (env: `GEMINI_API_KEY`, `GEMINI_VISION_MODEL`)

For `compare`, Tongyi Qwen's native multimodal embedding is preferred; OpenAI/Gemini fall back to a "describe-then-text-embed" strategy.

## Usage

Run the script with Python and a subcommand. It prints the model's text reply (analyze/ocr/detect) or a similarity score (compare).

### analyze — image description / visual QA

```bash
# Describe the image
python scripts/vision.py analyze --image cat.jpg

# Ask a question
python scripts/vision.py analyze --image cat.jpg --prompt "图里有几只猫?"
```

### ocr — extract text

```bash
python scripts/vision.py ocr --image doc.png --language zh
# → prints extracted text, preserving line breaks
```

### detect — object detection

```bash
python scripts/vision.py detect --image street.jpg
# → prints one line per object: label (confidence%) - 9-grid position
```

### compare — image similarity

```bash
python scripts/vision.py compare --image1 a.png --image2 b.png
# → prints similarity score 0.0~1.0 and the embedding provider used
```

### Arguments

All `image` / `image1` / `image2` args accept: **local path** / **HTTP(S) URL** / **data URL**.

`--provider` is optional for every subcommand (`openai` / `qwen` / `gemini`); omit to use the default (first configured provider). If the chosen provider fails, the script auto-tries the others.

## Workflow for the agent

1. **Prefer the MCP tools first.** If the MCP server is connected, call the matching MCP tool (`analyze_image` / `ocr` / `detect_objects` / `compare_images` — they also auto-fall back across providers). Only proceed to this Skill script if the MCP tool is unavailable, fails, or times out.
2. Identify the operation from the user's intent (see the table above).
3. Pick a provider:
   - If the user names one (e.g. "用通义分析"), use it.
   - Otherwise prefer `qwen` for Chinese prompts, `openai` for English, `gemini` as fallback. Only choose a provider whose API key is set in the environment.
4. Run the script via `RunCommand` (Python). The script auto-tries other configured providers if the first one fails. If it fails with "未配置任何 provider" or "所有 provider 调用均失败", tell the user which API key to set and stop.
5. Report the text result (analyze/ocr/detect) or similarity score (compare) to the user.

## Environment variables

At least one provider key must be set. The script reuses the same keys as the MCP server:

```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1     # optional, OpenAI-compatible endpoints
OPENAI_VISION_MODEL=gpt-4o

DASHSCOPE_API_KEY=sk-...
QWEN_VL_MODEL=qwen-vl-plus

GEMINI_API_KEY=...
GEMINI_VISION_MODEL=gemini-2.0-flash
```

### Skill-independent config (optional)

To give the Skill a **different** key / endpoint / model than MCP, set `SKILL_*`-prefixed vars. The Skill reads `SKILL_<name>` first, falling back to `<name>`:

```
SKILL_OPENAI_API_KEY=sk-skill-...             # Skill 用单独的 OpenAI Key
SKILL_OPENAI_BASE_URL=https://my-proxy/v1      # Skill 用单独的端点
SKILL_OPENAI_VISION_MODEL=gpt-4o
SKILL_DASHSCOPE_API_KEY=sk-skill-qwen-...
SKILL_QWEN_VL_MODEL=qwen-vl-plus
SKILL_GEMINI_API_KEY=...
SKILL_GEMINI_VISION_MODEL=gemini-2.0-flash
```

MCP server does not read `SKILL_*` vars, so its behavior is unaffected.

## Notes

- The script is standalone and shares `providers/` with the MCP server, so all three providers are supported with no extra setup.
- The script must be run from the project root so it can import `providers/`. If run elsewhere, use an absolute path and ensure `providers/` is importable.
