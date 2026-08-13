#!/usr/bin/env node
/**
 * 交互式配置向导 —— 支持多选所有 provider, 同时配置多个服务商。
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
// baseUrlKey: null = 不需要 Base URL; 字符串 = 对应的 env 变量名
const PROVIDERS = [
  {
    id: "openai",
    label: "OpenAI (GPT-4o / DALL-E 3)",
    keyName: "OPENAI_API_KEY",
    baseUrlKey: "OPENAI_BASE_URL",
    baseUrlDefault: "https://api.openai.com/v1",
    models: {
      OPENAI_VISION_MODEL: "gpt-4o",
      OPENAI_IMAGE_MODEL: "dall-e-3",
      OPENAI_EMBEDDING_MODEL: "text-embedding-3-small",
    },
  },
  {
    id: "qwen",
    label: "通义千问 / DashScope (Qwen-VL / 万相)",
    keyName: "DASHSCOPE_API_KEY",
    baseUrlKey: null,
    models: {
      QWEN_VL_MODEL: "qwen-vl-plus",
      QWEN_IMAGE_MODEL: "wanx2.1-t2i-turbo",
      QWEN_EMBEDDING_MODEL: "multimodal-embedding-one-peace-v1",
    },
  },
  {
    id: "gemini",
    label: "Google Gemini (Gemini 2.0 Flash / Imagen 3)",
    keyName: "GEMINI_API_KEY",
    baseUrlKey: null,
    models: {
      GEMINI_VISION_MODEL: "gemini-2.0-flash",
      GEMINI_IMAGE_MODEL: "imagen-3.0-generate-002",
      GEMINI_EMBEDDING_MODEL: "text-embedding-004",
    },
  },
  {
    id: "anthropic",
    label: "Anthropic Claude (视觉分析, 不支持生图)",
    keyName: "ANTHROPIC_API_KEY",
    baseUrlKey: "ANTHROPIC_BASE_URL",
    baseUrlDefault: "https://api.anthropic.com",
    models: {
      ANTHROPIC_VISION_MODEL: "claude-sonnet-4-20250514",
    },
    extra: { ANTHROPIC_API_VERSION: "2023-06-01" },
    note: "Claude 仅支持视觉分析 (OCR/检测/描述/问答), 生图和 embedding 会自动降级到其他 provider",
  },
  {
    id: "openai-custom",
    label: "自定义 OpenAI 兼容端点 (中转 / 自部署)",
    keyName: "OPENAI_API_KEY",
    baseUrlKey: "OPENAI_BASE_URL",
    baseUrlDefault: "https://your-endpoint.com/v1",
    models: {
      OPENAI_VISION_MODEL: "",
      OPENAI_IMAGE_MODEL: "",
      OPENAI_EMBEDDING_MODEL: "",
    },
    note: "模型 ID 可跳过, 启动时自动获取",
  },
  {
    id: "anthropic-custom",
    label: "自定义 Anthropic 兼容端点 (中转 / 自部署)",
    keyName: "ANTHROPIC_API_KEY",
    baseUrlKey: "ANTHROPIC_BASE_URL",
    baseUrlDefault: "https://your-anthropic-proxy.com",
    models: {
      ANTHROPIC_VISION_MODEL: "",
    },
    extra: { ANTHROPIC_API_VERSION: "2023-06-01" },
    note: "兼容端点 (如代理/中转), 模型 ID 可跳过",
  },
];

// ── 工具函数 ────────────────────────────────────────────────

function ask(rl, question, defaultValue) {
  const hint = defaultValue ? ` (默认: ${defaultValue})` : "";
  return new Promise((resolve) => {
    rl.question(`  ${question}${hint}: `, (answer) => {
      const trimmed = answer.trim();
      if (!trimmed && defaultValue !== undefined && defaultValue !== "") {
        return resolve(defaultValue);
      }
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

/** 配置单个 provider, 返回收集到的 config 键值对 */
async function configureProvider(rl, provider, existing) {
  console.log(`\n  ── 配置 ${provider.label} ──\n`);

  if (provider.note) {
    console.log(`  提示: ${provider.note}\n`);
  }

  const config = {};

  // API Key
  const existingKey = existing[provider.keyName] || "";
  const keyHint = existingKey ? ` (已配置: ${existingKey.slice(0, 8)}...)` : "";
  const apiKey = await ask(rl, `输入 ${provider.keyName}${keyHint}`, "");
  if (apiKey) {
    config[provider.keyName] = apiKey;
  } else if (existingKey) {
    console.log("  (保留已有 Key)");
  } else {
    console.log("  ⚠ 未输入 API Key, 跳过此 provider");
    return config;
  }

  // Base URL
  if (provider.baseUrlKey) {
    const existingUrl = existing[provider.baseUrlKey] || "";
    const urlDefault = provider.baseUrlDefault || existingUrl;
    const baseUrl = await ask(rl, `输入 Base URL`, urlDefault);
    if (baseUrl) config[provider.baseUrlKey] = baseUrl;
  }

  // Extra (如 ANTHROPIC_API_VERSION)
  if (provider.extra) {
    for (const [k, v] of Object.entries(provider.extra)) {
      const val = await ask(rl, `输入 ${k}`, v);
      if (val) config[k] = val;
    }
  }

  // 模型 ID (MODID) —— 可跳过
  console.log("");
  for (const [mk, defaultVal] of Object.entries(provider.models)) {
    const existingVal = existing[mk] || "";
    if (defaultVal) {
      const val = await ask(rl, `输入 ${mk}`, defaultVal);
      if (val) config[mk] = val;
    } else {
      const val = await ask(rl, `输入 ${mk} (可跳过, 启动时自动获取)`, existingVal);
      if (val) config[mk] = val;
    }
  }

  return config;
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
  console.log("  ║     支持多选, 可同时配置所有 provider            ║");
  console.log("  ╚══════════════════════════════════════════════════╝");
  console.log("");

  // 1. 多选 provider
  console.log("  第 1 步:选择要配置的 AI 服务商 (可多选)\n");
  PROVIDERS.forEach((p, i) => {
    console.log(`    ${i + 1}. ${p.label}`);
  });
  console.log("");
  console.log("  输入序号, 逗号分隔 (如 1,3,4)");
  console.log("  输入 a = 全选所有 provider");
  console.log("  回车 = 仅配置 OpenAI (默认)");
  console.log("");

  const answer = await ask(rl, "请输入", "");
  let selected = [];

  if (answer.toLowerCase() === "a") {
    selected = PROVIDERS.slice();
  } else if (answer) {
    const indices = answer
      .split(/[,，\s]+/)
      .map((s) => parseInt(s, 10) - 1)
      .filter((i) => i >= 0 && i < PROVIDERS.length);
    selected = indices.map((i) => PROVIDERS[i]);
  } else {
    selected = [PROVIDERS[0]]; // 默认 OpenAI
  }

  if (selected.length === 0) {
    console.log("\n  未选择任何 provider, 退出。");
    rl.close();
    return;
  }

  console.log(`\n  已选择 ${selected.length} 个 provider:`);
  selected.forEach((p, i) => console.log(`    ${i + 1}. ${p.label}`));
  console.log("");

  // 2. 依次配置每个 provider
  console.log("  第 2 步:依次配置每个 provider\n");

  const existing = readEnv(ENV_FILE);
  const config = { ...existing };

  for (const provider of selected) {
    const collected = await configureProvider(rl, provider, existing);
    Object.assign(config, collected);
  }

  // 3. 写入文件
  console.log("\n  第 3 步:保存配置\n");
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

  // 4. 完成
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
