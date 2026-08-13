#!/usr/bin/env node
/**
 * 交互式配置向导 —— 收集 provider / API Key / Base URL / 模型 ID。
 *
 * 运行方式:
 *   vision-toolkit --configure       (通过 CLI)
 *   node bin/configure.js            (直接运行)
 *   postinstall 自动调用              (npm install 后)
 *
 * 配置写入 ~/.vision-toolkit.env, server.py 启动时自动加载。
 * 模型 ID (MODID) 可跳过, server 启动时会尝试通过 API 自动获取。
 */
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const readline = require("node:readline");

const ENV_FILE = path.join(os.homedir(), ".vision-toolkit.env");

// ── Provider 预设 ───────────────────────────────────────────
const PROVIDERS = {
  "1": {
    label: "OpenAI (GPT-4o / DALL-E 3)",
    prefix: "OPENAI",
    defaults: {
      OPENAI_BASE_URL: "https://api.openai.com/v1",
      OPENAI_VISION_MODEL: "gpt-4o",
      OPENAI_IMAGE_MODEL: "dall-e-3",
      OPENAI_EMBEDDING_MODEL: "text-embedding-3-small",
    },
    keyName: "OPENAI_API_KEY",
  },
  "2": {
    label: "通义千问 / DashScope (Qwen-VL / 万相)",
    prefix: "DASHSCOPE",
    defaults: {
      QWEN_VL_MODEL: "qwen-vl-plus",
      QWEN_IMAGE_MODEL: "wanx2.1-t2i-turbo",
      QWEN_EMBEDDING_MODEL: "multimodal-embedding-one-peace-v1",
    },
    keyName: "DASHSCOPE_API_KEY",
  },
  "3": {
    label: "Google Gemini (Gemini 2.0 Flash / Imagen 3)",
    prefix: "GEMINI",
    defaults: {
      GEMINI_VISION_MODEL: "gemini-2.0-flash",
      GEMINI_IMAGE_MODEL: "imagen-3.0-generate-002",
      GEMINI_EMBEDDING_MODEL: "text-embedding-004",
    },
    keyName: "GEMINI_API_KEY",
  },
  "4": {
    label: "Anthropic Claude (视觉分析, 不支持生图)",
    prefix: "ANTHROPIC",
    defaults: {
      ANTHROPIC_BASE_URL: "https://api.anthropic.com",
      ANTHROPIC_VISION_MODEL: "claude-sonnet-4-20250514",
      ANTHROPIC_API_VERSION: "2023-06-01",
    },
    keyName: "ANTHROPIC_API_KEY",
    needsBaseUrl: true,
    note: "Claude 仅支持视觉分析 (OCR/检测/描述/问答), 生图和 embedding 请配置其他 provider",
  },
  "5": {
    label: "自定义 OpenAI 兼容端点 (中转 / 自部署)",
    prefix: "OPENAI",
    defaults: {
      OPENAI_BASE_URL: "https://your-endpoint.com/v1",
      OPENAI_VISION_MODEL: "",
      OPENAI_IMAGE_MODEL: "",
      OPENAI_EMBEDDING_MODEL: "",
    },
    keyName: "OPENAI_API_KEY",
  },
};

// ── 工具函数 ────────────────────────────────────────────────

function ask(rl, question, defaultValue) {
  const hint = defaultValue ? ` (默认: ${defaultValue})` : "";
  return new Promise((resolve) => {
    rl.question(`  ${question}${hint}: `, (answer) => {
      const trimmed = answer.trim();
      if (!trimmed && defaultValue) return resolve(defaultValue);
      resolve(trimmed);
    });
  });
}

/** 读取已有 .env 为 { KEY: VALUE } 对象 */
function readEnv(filePath) {
  const map = {};
  if (!fs.existsSync(filePath)) return map;
  const content = fs.readFileSync(filePath, "utf8");
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    // 去掉引号
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    map[key] = val;
  }
  return map;
}

/** 写入 .env (合并, 不删除已有键) */
function writeEnv(filePath, config) {
  const lines = [
    "# Vision Toolkit 配置文件",
    "# 由 vision-toolkit --configure 自动生成",
    `# 更新时间: ${new Date().toISOString()}`,
    "",
  ];
  for (const [key, val] of Object.entries(config)) {
    if (val) {
      lines.push(`${key}=${val.includes(" ") ? `"${val}"` : val}`);
    }
  }
  fs.writeFileSync(filePath, lines.join("\n") + "\n", "utf8");
}

// ── 主流程 ──────────────────────────────────────────────────

async function run() {
  // 非 TTY 跳过
  if (!process.stdin.isTTY) {
    console.log("[vision-toolkit] 非交互式环境, 配置向导已跳过。");
    console.log("[vision-toolkit] 请手动运行: vision-toolkit --configure");
    return;
  }

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  console.log("");
  console.log("  ╔══════════════════════════════════════════════════╗");
  console.log("  ║     Vision Toolkit — 配置向导                    ║");
  console.log("  ╚══════════════════════════════════════════════════╝");
  console.log("");

  // 1. 选择 provider
  console.log("  第 1 步:选择 AI 服务商\n");
  for (const [id, p] of Object.entries(PROVIDERS)) {
    console.log(`    ${id}. ${p.label}`);
  }
  console.log("");
  const choice = await ask(rl, "输入序号 (1-5)", "1");
  const provider = PROVIDERS[choice] || PROVIDERS["1"];

  console.log(`\n  已选择: ${provider.label}\n`);
  if (provider.note) {
    console.log(`  提示: ${provider.note}\n`);
  }

  // 2. API Key
  console.log("  第 2 步:配置 API Key\n");
  const apiKey = await ask(rl, `输入 ${provider.keyName}`);
  if (!apiKey) {
    console.log("\n  ⚠ 未输入 API Key, 你可以稍后手动编辑 ~/.vision-toolkit.env");
  }

  // 3. Base URL (OpenAI / Anthropic / 自定义需要)
  console.log("\n  第 3 步:配置 API 地址 (Base URL)\n");
  let baseUrl = "";
  if (provider.defaults.OPENAI_BASE_URL !== undefined) {
    baseUrl = await ask(rl, "输入 Base URL", provider.defaults.OPENAI_BASE_URL);
  } else if (provider.defaults.ANTHROPIC_BASE_URL !== undefined) {
    baseUrl = await ask(rl, "输入 Base URL", provider.defaults.ANTHROPIC_BASE_URL);
  } else if (choice === "2") {
    console.log("  (DashScope 无需 Base URL, 跳过)");
  } else if (choice === "3") {
    console.log("  (Gemini 无需 Base URL, 跳过)");
  }

  // 4. 模型 ID (MODID) —— 可跳过
  console.log("\n  第 4 步:配置模型 ID (MODID)\n");
  console.log("  提示: 可跳过, server 启动时会尝试通过 API 自动获取可用模型。\n");

  const existing = readEnv(ENV_FILE);
  const config = { ...existing };

  // 写入 API Key
  if (apiKey) config[provider.keyName] = apiKey;
  // 写入 Base URL (区分 OpenAI / Anthropic)
  if (baseUrl) {
    if (provider.defaults.ANTHROPIC_BASE_URL !== undefined) {
      config.ANTHROPIC_BASE_URL = baseUrl;
    } else {
      config.OPENAI_BASE_URL = baseUrl;
    }
  }

  // 收集模型配置
  const modelKeys = Object.keys(provider.defaults).filter((k) => k.endsWith("_MODEL"));
  for (const mk of modelKeys) {
    const defaultVal = provider.defaults[mk];
    const shortName = mk.replace(/^[A-Z]+_/, "").toLowerCase();
    if (choice === "5" && !defaultVal) {
      // 自定义端点, 无默认值, 可跳过
      const val = await ask(rl, `输入 ${mk} (可跳过, 启动时自动获取)`, "");
      if (val) config[mk] = val;
    } else {
      const val = await ask(rl, `输入 ${mk}`, defaultVal);
      if (val) config[mk] = val;
    }
  }

  // 5. 写入文件
  console.log("\n  第 5 步:保存配置\n");
  try {
    writeEnv(ENV_FILE, config);
    console.log(`  ✓ 配置已写入: ${ENV_FILE}`);
  } catch (e) {
    console.log(`  ✗ 写入失败: ${e.message}`);
    console.log("  请手动创建该文件, 参考格式:");
    for (const [k, v] of Object.entries(config)) {
      if (v) console.log(`    ${k}=${v}`);
    }
  }

  // 6. 完成
  console.log("");
  console.log("  ════════════════════════════════════════════════");
  console.log("  ✓ 配置完成!");
  console.log("  ════════════════════════════════════════════════");
  console.log("");
  console.log(`  配置文件: ${ENV_FILE}`);
  console.log("  如需修改, 重新运行: vision-toolkit --configure");
  console.log("");

  rl.close();
}

module.exports = { run, ENV_FILE, readEnv, writeEnv };

// 直接运行时自动执行
if (require.main === module) {
  run().catch(() => process.exit(0));
}
