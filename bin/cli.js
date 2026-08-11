#!/usr/bin/env node
/**
 * vision-toolkit 命令行入口 (Node.js 包装器)。
 *
 * 作用: 让用户能通过 `npx vision-toolkit` 或 `npm install -g vision-toolkit` 直接运行,
 *       内部 spawn Python 运行同目录下的 server.py。
 *
 * 用法:
 *   vision-toolkit                              # 以 stdio 模式启动 (MCP 客户端默认)
 *   vision-toolkit --transport sse --port 8765  # 以 SSE 模式启动
 *   vision-toolkit --python /path/to/python     # 指定 Python 解释器
 *   vision-toolkit --setup                      # 安装 Python 依赖后退出
 *
 * 环境变量:
 *   VISION_TOOLKIT_PYTHON  指定 Python 解释器路径 (同 --python)
 *   OPENAI_API_KEY / DASHSCOPE_API_KEY / GEMINI_API_KEY  provider 密钥
 */
"use strict";

const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const PKG_DIR = path.join(__dirname, "..");
const SERVER = path.join(PKG_DIR, "server.py");
const REQUIREMENTS = path.join(PKG_DIR, "requirements.txt");

// ---- 1. 解析 --python / --setup 这两个本包装器专属参数 ----
const argv = process.argv.slice(2);
let pythonCmd = process.env.VISION_TOOLKIT_PYTHON || "";
let setupOnly = false;
const passthrough = [];

for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === "--python" || a === "-p") {
    pythonCmd = argv[++i];
  } else if (a === "--setup") {
    setupOnly = true;
  } else {
    passthrough.push(a);
  }
}

// ---- 2. 探测可用的 Python 解释器 ----
function tryPython(cmd) {
  return new Promise((resolve) => {
    if (!cmd) return resolve(false);
    const p = spawn(cmd, ["-c", "import sys, mcp, httpx; print(sys.version)"], {
      stdio: ["ignore", "pipe", "pipe"],
      shell: true,
    });
    let ok = false;
    p.stdout.on("data", () => (ok = true));
    p.on("error", () => resolve(false));
    p.on("close", () => resolve(ok));
  });
}

async function detectPython() {
  const candidates = [
    pythonCmd,
    "python3",
    "python",
    "py",
    process.env.VISION_TOOLKIT_PYTHON,
  ].filter(Boolean);
  for (const c of candidates) {
    // 先验证它能 import 关键依赖
    if (await tryPython(c)) return c;
  }
  // 依赖缺失时, 至少返回一个存在的解释器, 由 setup 补依赖
  for (const c of candidates) {
    const ok = await new Promise((resolve) => {
      const p = spawn(c, ["--version"], {
        stdio: ["ignore", "pipe", "pipe"],
        shell: true,
      });
      p.on("error", () => resolve(false));
      p.on("close", (code) => resolve(code === 0));
    });
    if (ok) return c;
  }
  return null;
}

// ---- 3. 安装 Python 依赖 ----
function installDeps(python) {
  return new Promise((resolve) => {
    console.error("[vision-toolkit] 正在安装 Python 依赖 (requirements.txt) ...");
    const p = spawn(
      python,
      ["-m", "pip", "install", "-r", REQUIREMENTS],
      { stdio: "inherit", shell: true }
    );
    p.on("error", (e) => {
      console.error("[vision-toolkit] 依赖安装失败:", e.message);
      resolve(false);
    });
    p.on("close", (code) => {
      if (code === 0) console.error("[vision-toolkit] 依赖安装完成。");
      else console.error(`[vision-toolkit] pip 退出码 ${code}, 请手动运行: ${python} -m pip install -r requirements.txt`);
      resolve(code === 0);
    });
  });
}

// ---- 4. 主流程 ----
async function main() {
  if (!fs.existsSync(SERVER)) {
    console.error(`[vision-toolkit] 找不到 server.py: ${SERVER}`);
    process.exit(1);
  }

  const python = await detectPython();
  if (!python) {
    console.error(
      "[vision-toolkit] 未找到可用的 Python 解释器。\n" +
        "请安装 Python 3.10+, 或通过 --python <路径> / 环境变量 VISION_TOOLKIT_PYTHON 指定。"
    );
    process.exit(1);
  }

  // 依赖缺失时自动安装一次
  const depsOk = await tryPython(python);
  if (!depsOk) {
    await installDeps(python);
  }

  if (setupOnly) {
    console.error(`[vision-toolkit] 使用 Python: ${python}`);
    return;
  }

  // 透传其余参数给 server.py
  const args = [SERVER, ...passthrough];
  const child = spawn(python, args, { stdio: "inherit", shell: true });

  child.on("error", (e) => {
    console.error("[vision-toolkit] 启动失败:", e.message);
    process.exit(1);
  });
  child.on("close", (code) => process.exit(code ?? 0));

  // 转发终止信号
  for (const sig of ["SIGINT", "SIGTERM"]) {
    process.on(sig, () => child.kill(sig));
  }
}

main();
