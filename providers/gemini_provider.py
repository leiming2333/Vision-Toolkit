"""Google Gemini provider (Gemini 2.0 视觉 / Imagen 3 生图 / 文本 embedding)。"""
from __future__ import annotations

import os
from typing import Any

import httpx

from image_utils import resolve_image
from providers import env
from providers.base import VisionProvider


class GeminiProvider(VisionProvider):
    name = "gemini"
    supports_embedding = True

    def __init__(self) -> None:
        self.api_key = env("GEMINI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY 未设置")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.vision_model = env("GEMINI_VISION_MODEL", "gemini-2.0-flash")
        self.image_model = env(
            "GEMINI_IMAGE_MODEL", "imagen-3.0-generate-002"
        )
        self.embedding_model = env(
            "GEMINI_EMBEDDING_MODEL", "text-embedding-004"
        )

    async def analyze(self, image: str, prompt: str, **kwargs: Any) -> str:
        img = await resolve_image(image)
        model = kwargs.get("model", self.vision_model)
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": img["mime_type"],
                                "data": img["base64"],
                            }
                        },
                        {"text": prompt},
                    ]
                }
            ]
        }
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=body,
            )
            r.raise_for_status()
            parts = r.json()["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        model = kwargs.get("model", self.image_model)
        body = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1},
        }
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                f"{self.base_url}/models/{model}:predict?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=body,
            )
            r.raise_for_status()
            b64 = r.json()["predictions"][0]["bytesBase64Encoded"]
            return f"data:image/png;base64,{b64}"

    async def embed(self, image: str) -> list[float]:
        # Gemini 无公开的图像 embedding: 先描述, 再对文本做 embedding
        desc = await self.analyze(
            image, "Describe this image in detail for retrieval."
        )
        body = {
            "model": f"models/{self.embedding_model}",
            "content": {"parts": [{"text": desc}]},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.base_url}/models/{self.embedding_model}:embedContent"
                f"?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=body,
            )
            r.raise_for_status()
            return r.json()["embedding"]["values"]
