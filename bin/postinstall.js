#!/usr/bin/env node
/**
 * npm postinstall 钩子: 检测 Python 并尝试安装依赖。
 *
 * 设计原则: 失败绝不阻断 `npm install`。
 * 只打印提示, 始终 exit 0。依赖缺失会在首次运行 `vision-toolkit` 时再次尝试安装。
 */
"use strict";

const { spawn } = require("node:child_process");
const path = require("node:path");

const PKG_DIR = path.join(__dirname, "..");
const REQUIREMENTS = path.join(PKG_DIR, "requirements.txt");

function log(msg) {
  console.log(`[vision-toolkit postinstall] ${msg}`);
}

function run(cmd, args) {
  return new Promise((resolve) => {
    const p = spawn(cmd, args, { stdio: "ignore", shell: true });
    p.on("error", () => resolve(false));
    p.on("close", (code) => resolve(code === 0));
  });
}

async function main() {
  // 检测 Python
  let python = null;
  for (const c of ["python3", "python", "py"]) {
    if (await run(c, ["--version"])) {
      python = c;
      break;
    }
  }

  if (!python) {
    log(
      "未检测到 Python, 已跳过依赖安装。\n" +
        "  请安装 Python 3.10+ 后运行: npm run setup\n" +
        "  或通过 npx vision-toolkit --setup 在运行时自动安装。"
    );
    return;
  }
  log(`检测到 Python: ${python}`);

  // 尝试安装依赖 (失败不阻断)
  log("尝试安装 Python 依赖 ...");
  const ok = await run(python, ["-m", "pip", "install", "-r", REQUIREMENTS]);
  if (ok) {
    log("Python 依赖安装完成。");
  } else {
    log(
      "Python 依赖自动安装失败 (可能是权限或网络问题)。\n" +
        "  请手动运行: npm run setup\n" +
        "  或: " + python + " -m pip install -r requirements.txt"
    );
  }

  // 运行配置向导 (交互式收集 API Key / URL / 模型)
  try {
    const configure = require("./configure.js");
    await configure.run();
  } catch {
    // 配置向导失败不阻断安装
  }

  // 展示可接入的 AI Agent 列表
  console.log("");
  console.log("  ╔══════════════════════════════════════════════════════════════╗");
  console.log("  ║   Vision Toolkit 已安装完成 ✨                                ║");
  console.log("  ║   多模态视觉 MCP + 文生图 Skill (OpenAI/Qwen/Gemini/Claude)  ║");
  console.log("  ╚══════════════════════════════════════════════════════════════╝");
  console.log("");
  console.log("  ── 支持接入的 AI Agent ──────────────────────────────────────");
  console.log("");
  console.log("    1.  Trae                (原生 Skill + MCP, 最佳体验)");
  console.log("    2.  Claude Desktop      (mcpServers JSON)");
  console.log("    3.  Claude Code         (.mcp.json)");
  console.log("    4.  Cursor              (.cursor/mcp.json)");
  console.log("    5.  Windsurf            (mcp_config.json)");
  console.log("    6.  Cline               (cline_mcp_settings.json)");
  console.log("    7.  Roo Code            (.roo/mcp.json)");
  console.log("    8.  GitHub Copilot      (.vscode/mcp.json)");
  console.log("    9.  OpenCode            (opencode.json)");
  console.log("    10. Codex CLI           (~/.codex/config.toml)");
  console.log("    11. Continue            (~/.continue/config.yaml)");
  console.log("    12. Gemini CLI          (~/.gemini/settings.json)");
  console.log("    13. Zed                 (context_servers)");
  console.log("");
  console.log("  ── 快速接入 ─────────────────────────────────────────────────");
  console.log("");
  console.log("    复制以下配置到对应客户端的配置文件:");
  console.log("");
  console.log('      {');
  console.log('        "mcpServers": {');
  console.log('          "vision": {');
  console.log('            "command": "npx",');
  console.log('            "args": ["-y", "vision-toolkit"],');
  console.log('            "env": {');
  console.log('              "OPENAI_API_KEY": "sk-...",');
  console.log('              "DASHSCOPE_API_KEY": "sk-..."');
  console.log('            }');
  console.log('          }');
  console.log('        }');
  console.log('      }');
  console.log("");
  console.log("  ── 下一步 ───────────────────────────────────────────────────");
  console.log("");
  console.log("    1. 如未在配置向导中设置, 运行 vision-toolkit --configure 配置 API Key");
  console.log("    2. 复制上方配置到你的 Agent 配置文件 (详见文档)");
  console.log("    3. 重启对应 Agent 即可使用视觉工具");
  console.log("");
  console.log("  文档: https://github.com/leiming2333/Vision-Toolkit");
  console.log("");
}

main().finally(() => process.exit(0));
