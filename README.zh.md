# Vision Toolkit

> 多模态视觉 **MCP Server** + 独立 **Text-to-Image Skill**。
>
> 接入 **OpenAI GPT-4o · 通义千问 Qwen-VL · Google Gemini**:
> - **MCP 工具**:图像描述/问答、OCR、物体检测、文生图、图像相似度对比
> - **独立 Skill**:直接生图,任意 Agent 可用,无需启动 MCP Server

**中文** | [English](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)
[![Skill](https://img.shields.io/badge/TRAE-Skill-green.svg)](https://.)
[![npm](https://img.shields.io/badge/npm-vision--toolkit-red.svg)](https://www.npmjs.com/package/vision-toolkit)

---

## 目录

- [特性](#特性)
- [能力矩阵](#能力矩阵)
- [安装](#安装)
- [快速开始](#快速开始)
  - [方式一:启动 MCP Server(stdio,推荐接入客户端)](#方式一启动-mcp-serverstdio模式推荐接入客户端)
  - [方式二:SSE 远程模式](#方式二sse-远程模式)
  - [方式三:独立 Skill 脚本(无需 MCP,全 Agent 可用)](#方式三独立-skill-脚本无需-mcp全-agent-可用)
- [配置 Provider 密钥](#配置-provider-密钥)
- [在 MCP 客户端中接入](#在-mcp-客户端中接入)
  - [Trae(原生 Skill + MCP)](#trae原生-skill--mcp)
  - [使用 `mcpServers` JSON 格式的客户端](#使用-mcpservers-json-格式的客户端)
  - [Claude Code](#claude-code)
  - [OpenCode](#opencode)
  - [Codex CLI(OpenAI)](#codex-cliopenai)
  - [Continue](#continue)
  - [Gemini CLI](#gemini-cli)
  - [Zed](#zed)
  - [SSE 远程模式](#sse-远程模式)
- [暴露的 MCP 工具](#暴露的-mcp-工具)
- [文本生图 Skill](#文本生图-skill)
  - [生图降级策略](#生图降级策略)
  - [何时使用](#何时使用)
  - [直接调用脚本](#直接调用脚本)
  - [脚本参数](#脚本参数)
- [图像分析 Skill](#图像分析-skill)
  - [分析降级策略](#分析降级策略)
  - [何时使用](#何时使用-1)
  - [直接调用脚本](#直接调用脚本-1)
  - [子命令与参数](#子命令与参数)
- [CLI 参数](#cli-参数)
- [项目结构](#项目结构)
- [工作原理](#工作原理)
- [常见问题](#常见问题)
- [开发](#开发)
- [License](#license)

---

## 特性

- **MCP + Skill 双入口**:MCP server 提供图像理解/生图/对比 6 个工具;两个独立 Skill 让任意 Agent 都能直接生图、分析图像,无需连 MCP。
- **多模型聚合**:启动时按可用 API Key 自动装载 provider,工具调用时可通过参数切换。
- **6 个开箱即用的 MCP 工具**:图像描述/问答、OCR、物体检测、文生图、图像相似度对比、provider 列表。
- **Text-to-Image Skill**:独立于 MCP 协议,只要配置了 API Key,任何 Agent 都能通过 `scripts/generate_image.py` 调起生图。
- **Image Analysis Skill**:任何 Agent 都能通过 `scripts/vision.py` 对已有图像做描述/OCR/检测/对比,无需启动 MCP。
- **统一图像输入**:本地路径 / HTTP(S) URL / data URL 一律自动归一化。
- **双传输模式(MCP)**:stdio(本地客户端默认)与 SSE(远程/调试)。
- **npm 一键安装**:通过 `npx` / `npm i -g` 运行,内部自动管理 Python 依赖。
- **Provider 可插拔**:新增视觉模型只需继承 `VisionProvider` 并在注册表登记。

## 能力矩阵

| Provider | 视觉分析 | 文生图 | 图像 Embedding |
|----------|:--------:|:------:|:--------------:|
| **OpenAI** GPT-4o + DALL·E 3 | ✅ | ✅ | ⚠️ 描述兜底 |
| **通义千问** Qwen-VL + 万相 | ✅ | ✅ | ✅ 原生多模态 |
| **Google** Gemini + Imagen 3 | ✅ | ✅ | ⚠️ 描述兜底 |

> OpenAI / Gemini 暂无公开的图像 embedding 接口,采用「先描述再用文本 embedding」的兜底策略;通义千问 `multimodal-embedding-one-peace-v1` 为原生多模态图像向量化。

---

## 安装

Vision Toolkit 提供两种安装方式,任选其一。**前置条件**:Python 3.10+ 和至少一个 provider 的 API Key。

> **想接入某个 AI Agent?** 大部分支持 MCP 的客户端(Trae、Claude Desktop、Cursor、Windsurf、Cline、Continue、Roo Code、OpenCode、Codex CLI、Gemini CLI、Zed、GitHub Copilot、Claude Code)都能通过 `npx vision-toolkit` 自动拉起本工具。直接跳到 [在 MCP 客户端中接入](#在-mcp-客户端中接入) 查看各客户端的配置片段。

### 方式 A:通过 npm 安装(推荐,自动管理 Python 依赖)

```bash
# 1. 临时执行(无需安装)——MCP 客户端最常用的入口
npx vision-toolkit

# 2. 全局安装(之后 `vision-toolkit` 命令就在 PATH 上)
npm install -g vision-toolkit
vision-toolkit

# 3. 安装到当前项目
npm install vision-toolkit
npx vision-toolkit
```

首次运行时,Node 包装器会自动检测 Python 并尝试安装依赖(`mcp`、`httpx` 等)。
若自动安装失败,可手动执行:

```bash
npm run setup
# 或
vision-toolkit --setup
```

从 GitHub 安装也支持:

```bash
npm install -g github:leiming2333/Vision-Toolkit
```

### 方式 B:本地安装(clone + pip)

克隆源码并手动安装 Python 依赖。安装后既可启动 MCP server,也可直接使用独立 Skill 脚本。

```bash
git clone https://github.com/leiming2333/Vision-Toolkit.git
cd Vision-Toolkit
pip install -r requirements.txt

# 启动 MCP server
python server.py
# 或直接使用独立 Skill 脚本(无需 MCP):
python scripts/generate_image.py --prompt "a cat" --provider qwen --out cat.png
python scripts/vision.py analyze --image cat.jpg
```

> 安装完成后,请先阅读 [配置 Provider 密钥](#配置-provider-密钥) 设置 API Key。

---

## 快速开始

安装完成后(见上文 [安装](#安装)),按以下方式启动使用。

### 方式一:启动 MCP Server(stdio 模式,推荐接入客户端)

```bash
# 已通过 npm 安装
vision-toolkit
# 或临时运行
npx vision-toolkit

# 或手动 clone 安装
python server.py
```

启动后,在 MCP 客户端(Trae / Claude Desktop 等)的配置里接入即可。详见 [在 MCP 客户端中接入](#在-mcp-客户端中接入)。

### 方式二:SSE 远程模式

```bash
vision-toolkit --transport sse --host 0.0.0.0 --port 8765
```

### 方式三:独立 Skill 脚本(无需 MCP,全 Agent 可用)

不需要启动 MCP server,只要 API Key 已配好,任何 Agent 都能直接调用脚本:

```bash
# 文生图 Skill
python scripts/generate_image.py --prompt "赛博朋克风格的猫咪" --provider qwen --out cat.png
# → 输出 cat.png 的绝对路径

# 图像分析 Skill
python scripts/vision.py analyze --image cat.jpg --prompt "图里有什么?"
```

Skill 会自动被 TRAE 识别并在合适场景(用户说"画一张图/生成图片/画个..."或"描述/读取/检测/对比这张图")触发调用。

---

## 配置 Provider 密钥

至少配置**一个** provider 的 API Key 即可启动。多配可切换。

复制 [.env.example](.env.example) 为 `.env`,或直接设置系统环境变量:

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

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI 密钥 | — |
| `OPENAI_BASE_URL` | OpenAI 兼容端点(可填代理) | `https://api.openai.com/v1` |
| `OPENAI_VISION_MODEL` | 视觉模型 | `gpt-4o` |
| `OPENAI_IMAGE_MODEL` | 生图模型 | `dall-e-3` |
| `OPENAI_EMBEDDING_MODEL` | 文本 embedding 模型(用于图像相似度对比) | `text-embedding-3-small` |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope 密钥 | — |
| `QWEN_VL_MODEL` | Qwen 视觉模型 | `qwen-vl-plus` |
| `QWEN_IMAGE_MODEL` | 万相生图模型 | `wanx2.1-t2i-turbo` |
| `QWEN_EMBEDDING_MODEL` | 多模态 embedding 模型 | `multimodal-embedding-one-peace-v1` |
| `GEMINI_API_KEY` | Google AI 密钥 | — |
| `GEMINI_VISION_MODEL` | Gemini 视觉模型 | `gemini-2.0-flash` |
| `GEMINI_IMAGE_MODEL` | Imagen 生图模型 | `imagen-3.0-generate-002` |
| `GEMINI_EMBEDDING_MODEL` | 文本 embedding 模型(用于图像相似度对比) | `text-embedding-004` |

### Skill 独立配置(可选)

默认情况下,Skill 脚本与 MCP server 共用上面的环境变量,零额外配置。若希望 Skill 使用与 MCP **不同**的 Key / 端点 / 模型,可设置带 `SKILL_` 前缀的变量。Skill 运行时优先读 `SKILL_<name>`,未设置则回退到 `<name>`;MCP server **不读** `SKILL_*` 变量,因此 MCP 行为不受影响。

```bash
# 示例: Skill 用单独的 OpenAI 兼容端点和 Key
SKILL_OPENAI_API_KEY=sk-skill-...
SKILL_OPENAI_BASE_URL=https://my-proxy.example.com/v1
SKILL_OPENAI_IMAGE_MODEL=dall-e-3
SKILL_OPENAI_VISION_MODEL=gpt-4o

# 示例: Skill 用单独的通义 / Gemini Key
SKILL_DASHSCOPE_API_KEY=sk-skill-qwen-...
SKILL_GEMINI_API_KEY=...
```

上面的任意变量都可以加 `SKILL_` 前缀来仅为 Skill 覆盖(如 `SKILL_QWEN_IMAGE_MODEL`、`SKILL_GEMINI_VISION_MODEL`、`SKILL_OPENAI_EMBEDDING_MODEL`)。未设置的 `SKILL_*` 变量会直接回退到共用的值。

---

## 在 MCP 客户端中接入

Vision Toolkit 遵循标准 MCP 协议,任何兼容 MCP 的客户端都能接入。下面覆盖了 2026 年主流的 AI Agent,所有示例都假设你通过 `env`(或 shell)设置了 API Key,详见 [配置 Provider 密钥](#配置-provider-密钥)。

### Trae(原生 Skill + MCP)

Vision Toolkit 自带两个 TRAE 原生 Skill(`.trae/skills/`),所以 Trae 用户有最佳的开箱即用体验:工作区自动加载 Skill,**同时**可连接 MCP server 获得全部 6 个工具。

**方式 A —— UI(推荐):** 设置 → MCP → 添加 → 手动添加 → 粘贴下方 JSON。

**方式 B —— 项目级配置:** 在项目根目录创建 `.trae/mcp.json`(需先在 设置 → MCP 中开启"启用项目级 MCP"):

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

接入后,Trae 既会使用 MCP 工具(`analyze_image`、`generate_image` 等),**也会**自动识别 `.trae/skills/` 下的两个 Skill 用于独立生图 / 图像分析 —— 无需额外配置。

### 使用 `mcpServers` JSON 格式的客户端

下列客户端共享同一套 `mcpServers` JSON schema —— 同一段配置块复制到各自的配置文件即可:

| 客户端 | 配置文件位置 |
|--------|-------------|
| **Trae** | 工作区/全局 MCP 设置(UI 或 `mcp.json`) |
| **Claude Desktop** | macOS:`~/Library/Application Support/Claude/claude_desktop_config.json` · Windows:`%APPDATA%\Claude\claude_desktop_config.json` |
| **Cursor** | 全局:`~/.cursor/mcp.json` · 项目:`.cursor/mcp.json` |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` |
| **Cline**(VS Code) | `cline_mcp_settings.json`(Cline MCP 面板 → Configure) |
| **Roo Code**(VS Code) | 全局:`mcp_settings.json` · 项目:`.roo/mcp.json` |
| **GitHub Copilot**(VS Code) | `~/.vscode/mcp.json`(VS Code 1.102+)或 `.vscode/mcp.json` |

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

若已全局安装,可直接用二进制:

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

手动运行 Python(clone 安装):

```json
{
  "mcpServers": {
    "vision": {
      "command": "python",
      "args": ["C:\\path\\to\\Vision-Toolkit\\server.py"],
      "env": { "OPENAI_API_KEY": "sk-..." }
    }
  }
}
```

> 部分客户端(Cursor、Cline)编辑后热重载;Claude Desktop 需要完全重启。

### Claude Code

Claude Code 使用 `~/.claude.json`(用户级)或 `.mcp.json`(项目级),schema 与上面的 `mcpServers` JSON 相同。也可通过 CLI 添加:

```bash
claude mcp add vision --env OPENAI_API_KEY=sk-... --env DASHSCOPE_API_KEY=sk-... -- npx -y vision-toolkit
```

### OpenCode

OpenCode 使用 `opencode.json` / `opencode.jsonc`(在 `~/.config/opencode/` 或项目根目录),结构略有不同:`command` 是数组,且键名是 `mcp`(不是 `mcpServers`)。

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

### Codex CLI(OpenAI)

Codex 把 MCP 配置放在 `~/.codex/config.toml`,使用 TOML 格式。注意键名是 snake_case 的 `mcp_servers`(不是 `mcpServers`)。

```toml
[mcp_servers.vision]
command = "npx"
args = ["-y", "vision-toolkit"]
env = { OPENAI_API_KEY = "sk-...", DASHSCOPE_API_KEY = "sk-..." }
startup_timeout_sec = 20
```

或通过 CLI:

```bash
codex mcp add vision --env OPENAI_API_KEY=sk-... --env DASHSCOPE_API_KEY=sk-... -- npx -y vision-toolkit
```

用 `codex mcp list` 验证,或在 Codex TUI 里执行 `/mcp`。

### Continue

Continue 从 YAML 配置读取 MCP 服务器(`~/.continue/config.yaml` 或工作区 `.continue/mcpServers/<name>.yaml`)。

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

Gemini CLI 读取 `~/.gemini/settings.json`,接受标准 `mcpServers` JSON 格式。

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

Zed 把 MCP 服务器放在 `~/.config/zed/settings.json`(macOS:`~/Library/Application Support/Zed/settings.json`)的 `context_servers` 下。

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

### SSE 远程模式

在服务器上启动:

```bash
vision-toolkit --transport sse --host 0.0.0.0 --port 8765
```

客户端配置(JSON 客户端):

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

Codex CLI(TOML)—— 用 `url` 代替 `command`:

```toml
[mcp_servers.vision]
url = "http://your-server:8765/sse"
```

OpenCode(JSON):

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

## 暴露的 MCP 工具

| 工具 | 说明 | 关键参数 |
|------|------|----------|
| `list_providers` | 列出已配置的 provider 及能力 | — |
| `analyze_image` | 图像描述 / 视觉问答 | `image`, `prompt`, `provider?` |
| `ocr` | 提取图中文字 | `image`, `language?`, `provider?` |
| `detect_objects` | 物体检测(标签+置信度+九宫格位置) | `image`, `provider?` |
| `generate_image` | 文生图,返回 data URL | `prompt`, `size?`, `provider?` |
| `compare_images` | 图像相似度对比(余弦相似度 0~1) | `image1`, `image2`, `provider?` |

所有 `image` 参数统一支持:**本地路径** / **HTTP(S) URL** / **data URL**。

`provider` 参数可选值为 `openai` / `qwen` / `gemini`,省略则使用默认(第一个已配置的 provider)。

### 调用示例

```
工具: analyze_image
参数: { "image": "https://example.com/cat.jpg", "prompt": "图里有几只猫?" }

工具: generate_image
参数: { "prompt": "赛博朋克风格的猫咪", "size": "1024x1024", "provider": "qwen" }

工具: compare_images
参数: { "image1": "./a.png", "image2": "https://example.com/b.png" }
```

---

## 文本生图 Skill

项目内置了一个 TRAE **Skill**(.trae/skills/text-to-image/),让**任意 Agent** 都能在任何场景直接生成图像,无需启动 MCP server。

它调用的是同一份 `providers/` 代码,所以和 MCP 的 `generate_image` 工具行为一致、支持的 provider 相同。

### 生图降级策略

Vision Toolkit 对文生图采用**分层降级**:**默认优先用 MCP 工具,只有 MCP 不可用或失败时才回退到 Skill 脚本**。

1. **优先 MCP `generate_image` 工具** —— MCP server 已连接时,AI 优先调用该工具。该工具内部同样会自动跨已配置的 provider 降级(如 `openai` → `qwen` → `gemini`):指定的 provider 出错时,会依次重试其他已配置的 provider,直到有一个成功或全部失败。
2. **失败时改用 Skill 脚本** —— 只有当 MCP 工具不可用、调用失败或超时,AI 才会改为运行 `scripts/generate_image.py`。脚本同样会在指定 provider 失败时自动尝试其他已配置的 provider。

**共用配置(单一来源)**:MCP 工具与 Skill 脚本读取**同一套**环境变量 —— `OPENAI_API_KEY` / `DASHSCOPE_API_KEY` / `GEMINI_API_KEY` 及对应的 `*_BASE_URL` / `*_IMAGE_MODEL`。Skill 没有独立配置,MCP 用什么,Skill 就用什么。若 MCP 那边配的 Key 缺失或不可用,Skill 也无法凭空补出一个 —— 此时提示用户设置相应环境变量即可。

### 何时使用

| 场景 | 用哪个? |
|------|--------|
| 在连了本项目的 MCP 客户端里(Trae、Claude Desktop 已配置 mcpServers) | 优先 `generate_image` 工具,AI 会自动用 |
| 没连 MCP、或想给**任意 Agent** 用、或写自动化脚本 | **Text-to-Image Skill** / 独立脚本 |

**Skill 触发时机**(用户的表述通常会包含:生成、画、绘制、做一张、制作、create / draw / generate / make an image/picture/illustration)。

### 直接调用脚本

脚本路径:[scripts/generate_image.py](scripts/generate_image.py)

```bash
# 基本用法:保存为本地 PNG,打印文件绝对路径
python scripts/generate_image.py --prompt "赛博朋克风格的猫咪" --provider qwen --out cat.png

# 中文 prompt 默认推荐 provider=qwen,英文 prompt 默认推荐 openai,gemini 兜底
python scripts/generate_image.py --prompt "a cozy mountain cabin at sunset" --provider openai

# 自定义尺寸
python scripts/generate_image.py --prompt "a cat" --size 1024x1792 --provider openai

# 只输出 data URL,不落盘(方便内嵌到 markdown/前端)
python scripts/generate_image.py --prompt "a cat" --provider qwen --data-url
```

### 脚本参数

| Flag | 缩写 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--prompt` | `-p` | ✅ | — | 图像描述,建议用英文或详细中文 |
| `--provider` | | 否 | `openai` | `openai` / `qwen` / `gemini`(只能选已配 API Key 的) |
| `--size` | | 否 | `1024x1024` | 图像尺寸,Qwen 会自动把 `x` 转成 `*` |
| `--out` | `-o` | 否 | `generated.png` | 落盘文件名,自动补 .png 后缀 |
| `--data-url` | | 否 | false | 只打印 `data:image/png;base64,...` 不写文件 |

### Agent 工作流(SKILL.md 内置指引)

Skill 里给 AI 写好了标准流程,AI 会按下面步骤执行:

1. 确认/润色 prompt(中文可直接用,必要时转更详细的描述)。
2. 选 provider:用户指定优先;否则**中文 prompt → qwen,英文 prompt → openai,gemini 兜底**;始终只选已配 Key 的。
3. 输出形式:**默认落盘**给用户路径;只有用户要求内嵌/嵌入时才用 `--data-url`。
4. 通过 `RunCommand` 调 Python 脚本;若报"未配置任何 provider",提示用户补 API Key。
5. 成功后向用户报告文件路径或 data URL。

### Skill 文件位置

```
vision-toolkit/.trae/skills/text-to-image/
└── SKILL.md   # TRAE 原生识别的 Skill 定义
```

把项目 clone 到本地并在 TRAE 中打开后,该 Skill 会自动被工作区加载。

---

## 图像分析 Skill

项目还内置了一个 TRAE **Skill**(.trae/skills/image-analysis/),让**任意 Agent** 都能直接理解**已有**图像,无需启动 MCP server。支持四种操作:图像描述/问答、OCR、物体检测、图像相似度对比。

它调用的是同一份 `providers/` 代码,所以和 MCP 的 `analyze_image` / `ocr` / `detect_objects` / `compare_images` 工具行为一致、支持的 provider 相同。

### 分析降级策略

Vision Toolkit 对图像理解同样采用**分层降级**:**默认优先用 MCP 工具,只有 MCP 不可用或失败时才回退到 Skill 脚本**。

1. **优先 MCP 工具** —— MCP server 已连接时,AI 优先调用 `analyze_image` / `ocr` / `detect_objects` / `compare_images`,无需 Skill。
2. **失败时改用 Skill 脚本** —— 只有当 MCP 工具不可用、调用失败或超时,AI 才会改为运行 `scripts/vision.py`。脚本同样会自动跨已配置的 provider 降级:指定的 provider 出错时,依次重试其他已配置的 provider。`compare` 优先用原生多模态 embedding 的 provider(通义千问),OpenAI/Gemini 回退到「描述 + 文本 embedding」兜底。

**共用配置(单一来源)**:MCP 工具与 Skill 脚本读取**同一套**环境变量 —— `OPENAI_API_KEY` / `DASHSCOPE_API_KEY` / `GEMINI_API_KEY` 及对应的 `*_BASE_URL` / `*_VISION_MODEL`。Skill 没有独立配置,MCP 用什么,Skill 就用什么。

### 何时使用

| 场景 | 用哪个? |
|------|--------|
| 在连了本项目的 MCP 客户端里 | 优先 MCP 工具(`analyze_image` / `ocr` / `detect_objects` / `compare_images`) |
| 没连 MCP、或想给**任意 Agent** 用、或写自动化脚本 | **Image Analysis Skill** / 独立脚本 |

**Skill 触发时机**(用户的表述通常会包含:描述、分析、理解、读取图中文字、OCR、检测图中物体、对比两张图)。

### 直接调用脚本

脚本路径:[scripts/vision.py](scripts/vision.py)

```bash
# 描述图像(默认 prompt)
python scripts/vision.py analyze --image cat.jpg

# 视觉问答
python scripts/vision.py analyze --image cat.jpg --prompt "图里有几只猫?"

# OCR 提取文字,可选语言提示
python scripts/vision.py ocr --image doc.png --language zh

# 物体检测(标签 + 置信度 + 九宫格位置)
python scripts/vision.py detect --image street.jpg

# 图像相似度对比(余弦相似度 0~1)
python scripts/vision.py compare --image1 a.png --image2 b.png
```

### 子命令与参数

所有 `image` / `image1` / `image2` 参数统一支持:**本地路径** / **HTTP(S) URL** / **data URL**。

`--provider` 每个子命令都可省略(`openai` / `qwen` / `gemini`),省略则用默认;指定 provider 失败会自动降级到其他。

| 子命令 | 参数 | 说明 |
|--------|------|------|
| `analyze` | `--image`(必填), `--prompt?`, `--provider?` | 图像描述 / 视觉问答 |
| `ocr` | `--image`(必填), `--language?`, `--provider?` | 提取图中文字,保留换行 |
| `detect` | `--image`(必填), `--provider?` | 物体检测(标签+置信度+九宫格位置) |
| `compare` | `--image1`(必填), `--image2`(必填), `--provider?` | 图像相似度对比(余弦 0~1) |

### Skill 文件位置

```
vision-toolkit/.trae/skills/image-analysis/
└── SKILL.md   # TRAE 原生识别的 Skill 定义
```

把项目 clone 到本地并在 TRAE 中打开后,该 Skill 会自动被工作区加载。

---

## CLI 参数

```bash
vision-toolkit [options]

选项:
  --transport <stdio|sse>   传输方式,默认 stdio
  --host <addr>             SSE 监听地址,默认 127.0.0.1
  --port <n>                SSE 监听端口,默认 8765
  --python <path>           指定 Python 解释器路径
  --setup                   仅安装 Python 依赖后退出
  -p <path>                 --python 的简写
```

也可用环境变量 `VISION_TOOLKIT_PYTHON` 指定 Python 解释器。

---

## 项目结构

```
vision-toolkit/
├── package.json                 # npm 包定义(bin / scripts / postinstall / files)
├── bin/
│   ├── cli.js                   # Node.js 命令入口,spawn Python server.py
│   └── postinstall.js           # npm 安装钩子,自动装 Python 依赖(失败不阻断)
├── server.py                    # MCP 主服务 + 6 个工具(理解/生图/对比)
├── image_utils.py               # 图像输入归一化(路径/URL/data URL)
├── providers/
│   ├── __init__.py              # provider 注册表
│   ├── base.py                  # 抽象基类 VisionProvider(analyze / generate / embed)
│   ├── openai_provider.py       # OpenAI: GPT-4o + DALL·E 3 + 文本 embedding
│   ├── qwen_provider.py         # 通义千问: Qwen-VL + 万相 + 多模态 embedding
│   └── gemini_provider.py       # Gemini + Imagen 3 + 文本 embedding
├── scripts/
│   ├── generate_image.py        # 独立文生图 CLI 脚本(text-to-image Skill 调用)
│   └── vision.py                # 独立视觉理解 CLI 脚本(image-analysis Skill 调用)
├── .trae/
│   └── skills/
│       ├── text-to-image/
│       │   └── SKILL.md         # TRAE Skill:何时/如何生图
│       └── image-analysis/
│           └── SKILL.md         # TRAE Skill:何时/如何分析/OCR/检测/对比
├── requirements.txt             # Python 依赖(MCP + Skill 共用)
├── .env.example                 # 环境变量模板
├── .gitignore                   # 避免提交缓存、.env 等
├── .npmignore                   # 发布 npm 包时排除的文件
├── LICENSE                      # MIT
├── README.md                    # English documentation (default)
└── README.zh.md                 # 中文说明文档
```

---

## 工作原理

```
  入口 A: MCP 客户端                    入口 B: 任意 Agent / 脚本
 (Trae / Claude Desktop)                  (TRAE Skill / CI / 手动)
          │                                          │
          │ stdio / SSE                              │ RunCommand
          ▼                                          ▼
  ┌───────────────────┐                  ┌──────────────────────────┐
  │  server.py        │                  │ scripts/generate_image.py│  (文生图)
  │  (MCP SDK, 6 tools)│                  │ scripts/vision.py        │  (图像分析)
  └─────────┬─────────┘                  └────────────┬─────────────┘
            │                                       │
            └─────────────── 共用 providers ────────┘
                                  │
                                  ▼
                   ┌───────────────────────────┐
                   │ 视觉/生图模型 HTTP API:    │
                   │ OpenAI / Qwen / Gemini    │
                   └───────────────────────────┘

  npm 入口包装(任选其一):
  └─────────────────────────────────────────────────┐
    npx vision-toolkit  ──► bin/cli.js ──► server.py
    (CLI 参数、Python 探测、自动 pip install 依赖)
  └─────────────────────────────────────────────────┘
```

### 入口 A —— MCP Server(图像理解 + 生图 + 对比)

1. 用户执行 `npx vision-toolkit`(或已在客户端配置 `mcpServers`),Node 包装器 `bin/cli.js` 启动。
2. 包装器探测可用 Python 解释器,必要时自动 `pip install` 依赖。
3. 包装器 `spawn` Python 运行 `server.py`,透传全部参数与 stdio。
4. `server.py` 通过官方 `mcp` SDK 注册 6 个工具,按 API Key 装载 provider。
5. MCP 客户端通过 stdio/SSE 调用工具,server 转发到对应视觉模型 API。

### 入口 B —— 独立 Skill(全 Agent 可用,无需 MCP)

项目内置两个 Skill,各由一个独立脚本支撑:

- **Text-to-Image Skill** → `scripts/generate_image.py`(文生图)
- **Image Analysis Skill** → `scripts/vision.py`(描述 / OCR / 检测 / 对比已有图像)

1. 用户说"生成/画一张图..."或"描述/读取/检测/对比这张图...",TRAE 识别到对应的 `.trae/skills/*/SKILL.md` 并激活 Skill。
2. AI 按 Skill 中的工作流选 provider 和操作。
3. AI 通过 `RunCommand` 直接调用对应脚本。
4. 脚本读取环境变量中的 API Key,共用 `providers/` 实现;失败时自动跨已配置 provider 降级。
5. 脚本输出结果(文件路径 / data URL / 文本 / 相似度),AI 把结果反馈给用户。

> 所有入口共用同一份 `providers/` 代码与同一份 API Key,因此行为、支持的模型完全一致。区别只是:入口 A 是**通过 MCP 协议**暴露所有能力;入口 B 是**脱离 MCP 协议**的轻量脚本,既可生图也可分析。

---

## 常见问题

**Q: `npm install` 时报 Python 依赖安装失败?**
A: postinstall 失败不会阻断安装。请手动运行 `npm run setup`,或 `vision-toolkit --setup`,首次运行时也会自动重试。

**Q: 没有配置任何 API Key 会怎样?**
A: 服务能启动但无 provider,调用工具会返回提示。`list_providers` 工具可查看当前可用 provider。

**Q: 如何使用 OpenAI 兼容的第三方端点?**
A: 设置 `OPENAI_BASE_URL` 指向该端点(如代理、Azure、本地 vLLM 等)。

**Q: 图像相似度的准确度?**
A: 通义千问原生多模态 embedding 最贴近图像内容;OpenAI/Gemini 为描述兜底,更偏向语义相似。

**Q: 支持本地部署的模型吗?**
A: 支持。把 `OPENAI_BASE_URL` 指向本地 OpenAI 兼容端点(如 vLLM、Ollama 的 OpenAI 接口)即可。

**Q: 为什么要有两条生图路径?(MCP 工具 vs Skill 脚本)**
A: 场景不同:
- **MCP `generate_image` 工具**:在连了 MCP server 的客户端里,AI 自动调用所有能力(理解/生图/对比),生图只是其中一环。
- **Text-to-Image Skill**:不依赖 MCP 连接,任意 Agent 都能用;适合独立生图任务、CI、批量脚本、Trae 里没配 MCP 时应急。

两者调用同一份代码,结果完全一致。图像分析同理:MCP 的 `analyze_image` / `ocr` / `detect_objects` / `compare_images` 工具 对应 **Image Analysis Skill**(`scripts/vision.py`)。

**Q: Text-to-Image Skill 在 TRAE 里没生效?**
A: 请确认:
1. 工作区根目录包含 `.trae/skills/text-to-image/SKILL.md`(即 TRAE 打开的是 `vision-toolkit/` 或其上层目录)。
2. 对话触发词要明确,例如:"生成一张 xxx 的图"、"画一个"、"做一张图片"、"create an image"。
3. `scripts/generate_image.py` 能手动运行成功(先排除 Key/依赖问题)。

**Q: Image Analysis Skill 在 TRAE 里没生效?**
A: 同上排查,只是对应 `.trae/skills/image-analysis/SKILL.md` 和 `scripts/vision.py`。触发词:"描述/分析这张图"、"读取图里的文字 / OCR"、"检测图里的物体"、"对比这两张图"。

**Q: 可以只用 Skill 不用 MCP 吗?或者反过来只用 MCP?**
A: 完全可以。各入口独立:
- 只做生图 → 只用 Text-to-Image Skill,连 MCP server 都不用启动。
- 只做图像分析 → 只用 Image Analysis Skill,无需启动 MCP server。
- 只用 MCP → 6 个工具(理解/生图/对比)全可用,Skill 是可选的降级备份。
- 都要用 → 全开,AI 会根据场景自动选入口。

---

## 开发

### 新增一个 Provider

1. 在 `providers/` 下新建 `xxx_provider.py`,继承 `VisionProvider` 并实现 `analyze` / `generate`(/ `embed`)。
2. 在 [providers/__init__.py](providers/__init__.py) 的 `PROVIDER_CLASSES` 中登记。
3. 完成。工具调用时即可通过 `provider="xxx"` 切换。

### 本地调试

```bash
# 安装依赖
pip install -r requirements.txt

# 1) MCP stdio 模式(配合 MCP Inspector 调试工具)
npx @modelcontextprotocol/inspector python server.py

# 2) MCP SSE 模式
python server.py --transport sse --port 8765

# 3) Skill / 独立生图脚本(无需启动 MCP)
python scripts/generate_image.py --prompt "a test cat" --provider qwen --out test.png
```

### 发布到 npm

```bash
npm version patch
npm publish
```

> 发布前请把 `package.json` 中的 `homepage` / `repository.url` / `author` 改为你自己的。

---

## License

[MIT](LICENSE)

---

> English documentation: [README.md](README.md)
