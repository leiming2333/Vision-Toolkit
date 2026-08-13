"""Anthropic Claude provider (Claude 3.5 / 4 视觉分析)。

Claude 具备强大的视觉理解能力 (OCR / 物体检测 / 图像描述 / 问答),
但不原生支持文生图和图像 embedding —— 这两项会抛 NotImplementedError,
调用方应回退到其他 provider (OpenAI / Qwen / Gemini)。
"""
from __future__ import annotations

from typing import Any

import httpx

from image_utils import resolve_image
from providers import env
from providers.base import VisionProvider


class AnthropicProvider(VisionProvider):
    name = "anthropic"
    supports_generation = False
    supports_embedding = False

    def __init__(self) -> None:
        self.api_key = env("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY 未设置")
        self.base_url = env(
            "ANTHROPIC_BASE_URL", "https://api.anthropic.com"
        ).rstrip("/")
        self.vision_model = env("ANTHROPIC_VISION_MODEL", "claude-sonnet-4-20250514")
        self.api_version = env("ANTHROPIC_API_VERSION", "2023-06-01")

    async def analyze(self, image: str, prompt: str, **kwargs: Any) -> str:
        img = await resolve_image(image)
        body = {
            "model": kwargs.get("model", self.vision_model),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": img["mime_type"],
                                "data": img["base64"],
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{self.base_url}/v1/messages",
                headers=self._headers(),
                json=body,
            )
            r.raise_for_status()
            # content 是 list[{type: "text", text: "..."}]
            content = r.json().get("content", [])
            return "".join(
                block.get("text", "") for block in content if block.get("type") == "text"
            )

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError(
            "Anthropic Claude 不支持原生文生图, 请切换到 OpenAI / Qwen / Gemini provider。"
        )

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "Content-Type": "application/json",
        }
