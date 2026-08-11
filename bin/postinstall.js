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
}

main().finally(() => process.exit(0));
