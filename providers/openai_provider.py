"""OpenAI 兼容 provider (GPT-4o 视觉 / DALL-E 3 生图 / 文本 embedding)。

通过 OPENAI_BASE_URL 可指向任何 OpenAI 兼容端点(官方、代理、自建)。
图像 embedding 采用「先描述再用文本 embedding」的兜底策略
(OpenAI 暂无直接的图像 embedding 接口)。
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from image_utils import resolve_image
from providers import env
from providers.base import VisionProvider


class OpenAIProvider(VisionProvider):
    name = "openai"
    supports_embedding = True

    def __init__(self) -> None:
        self.api_key = env("OPENAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY 未设置")
        self.base_url = env(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        ).rstrip("/")
        self.vision_model = env("OPENAI_VISION_MODEL", "gpt-4o")
        self.image_model = env("OPENAI_IMAGE_MODEL", "dall-e-3")
        self.embedding_model = env(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )

    async def analyze(self, image: str, prompt: str, **kwargs: Any) -> str:
        img = await resolve_image(image)
        body = {
            "model": kwargs.get("model", self.vision_model),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": img["data_url"]}},
                    ],
                }
            ],
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=body,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        body = {
            "model": kwargs.get("model", self.image_model),
            "prompt": prompt,
            "n": 1,
            "size": kwargs.get("size", "1024x1024"),
            "response_format": "b64_json",
        }
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                f"{self.base_url}/images/generations",
                headers=self._headers(),
                json=body,
            )
            if r.status_code == 404:
                # 某些 OpenAI 兼容网关(如阿里云 Model Studio token-plan)不实现
                # /images/generations, 图像模型只能通过 /chat/completions 调用
                return await self._generate_via_chat(client, prompt, **kwargs)
            r.raise_for_status()
            b64 = r.json()["data"][0]["b64_json"]
            return f"data:image/png;base64,{b64}"

    async def _generate_via_chat(
        self, client: httpx.AsyncClient, prompt: str, **kwargs: Any
    ) -> str:
        """/images/generations 404 时的回退: 走 /chat/completions 多模态列表 content。"""
        body = {
            "model": kwargs.get("model", self.image_model),
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }
        r = await client.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json=body,
        )
        r.raise_for_status()
        payload = r.json()
        # 兼容 DashScope 原生信封: {"output": {"choices": [...]}}
        choices = payload.get("choices") or (payload.get("output") or {}).get("choices") or []
        for choice in choices:
            content = (choice.get("message") or {}).get("content")
            url = self._extract_image_url(content)
            if url:
                return url
        raise RuntimeError("chat/completions 回退响应中未找到图像 URL")

    @staticmethod
    def _extract_image_url(content: Any) -> str | None:
        """从 assistant content(字符串或 part 列表)中提取第一个图像 URL。"""
        if isinstance(content, str):
            return content if content.startswith(("http://", "https://", "data:")) else None
        if not isinstance(content, list):
            return None
        for part in content:
            if not isinstance(part, dict):
                continue
            # DashScope 风格: {"type": "image", "image": "<url>"} 或 {"image": "<url>"}
            url = part.get("image")
            if isinstance(url, str) and url.startswith(("http://", "https://", "data:")):
                return url
            # 标准 OpenAI 风格: {"type": "image_url", "image_url": {"url": "<url>"}}
            image_url = part.get("image_url")
            if isinstance(image_url, dict):
                url = image_url.get("url")
                if isinstance(url, str):
                    return url
            elif isinstance(image_url, str):
                return image_url
        return None

    async def embed(self, image: str) -> list[float]:
        # OpenAI 无原生图像 embedding: 先描述, 再对描述文本做 embedding
        desc = await self.analyze(
            image, "Describe this image in detail for retrieval.", max_tokens=512
        )
        body = {"model": self.embedding_model, "input": desc}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.base_url}/embeddings", headers=self._headers(), json=body
            )
            r.raise_for_status()
            return r.json()["data"][0]["embedding"]

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
