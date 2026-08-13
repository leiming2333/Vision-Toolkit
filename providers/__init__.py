"""provider 注册表。新增 provider 时在此登记即可。"""
from __future__ import annotations

import os

from providers.base import VisionProvider
from providers.openai_provider import OpenAIProvider
from providers.qwen_provider import QwenProvider
from providers.gemini_provider import GeminiProvider
from providers.anthropic_provider import AnthropicProvider


def env(name: str, default: str = "") -> str:
    """读取配置变量,支持 Skill 独立配置回退。

    优先级:
      1. SKILL_<name>  —— Skill 脚本独立配置(仅 Skill 运行时设置)
      2. <name>        —— MCP/Skill 共用配置

    MCP server 不会设置 SKILL_* 变量,因此 MCP 行为不受影响;
    Skill 脚本若设置了 SKILL_* 变量则用独立的,否则回退到共用的。

    注意: API Key 类变量(如 OPENAI_API_KEY)同样适用 ——
    设了 SKILL_OPENAI_API_KEY 就用 Skill 自己的 Key,否则用共用的。
    """
    skill_name = f"SKILL_{name}"
    if os.environ.get(skill_name):
        return os.environ[skill_name]
    return os.environ.get(name, default)


# name -> class
PROVIDER_CLASSES: dict[str, type[VisionProvider]] = {
    "openai": OpenAIProvider,
    "qwen": QwenProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
}

__all__ = [
    "VisionProvider",
    "PROVIDER_CLASSES",
    "OpenAIProvider",
    "QwenProvider",
    "GeminiProvider",
    "AnthropicProvider",
    "env",
]
