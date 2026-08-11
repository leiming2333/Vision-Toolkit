"""通义千问 / DashScope provider。

能力:
  - 视觉分析: Qwen-VL-Plus / Qwen-VL-Max (multimodal-generation)
  - 文生图:   万相 wanx2.1 (异步任务, 提交后轮询)
  - 图像 embedding: multimodal-embedding-one-peace-v1 (原生多模态, 真正按图像内容向量化)
"""
from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from image_utils import resolve_image
from providers import env
from providers.base import VisionProvider


class QwenProvider(VisionProvider):
    name = "qwen"
    supports_embedding = True

    def __init__(self) -> None:
        self.api_key = env("DASHSCOPE_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY 未设置")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.vision_model = env("QWEN_VL_MODEL", "qwen-vl-plus")
        self.image_model = env("QWEN_IMAGE_MODEL", "wanx2.1-t2i-turbo")
        self.embedding_model = env(
            "QWEN_EMBEDDING_MODEL", "multimodal-embedding-one-peace-v1"
        )

    async def analyze(self, image: str, prompt: str, **kwargs: Any) -> str:
        img = await resolve_image(image)
        body = {
            "model": kwargs.get("model", self.vision_model),
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": img["data_url"]},
                            {"text": prompt},
                        ],
                    }
                ]
            },
        }
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{self.base_url}/services/aigc/multimodal-generation/generation",
                headers=self._headers(),
                json=body,
            )
            r.raise_for_status()
            content = r.json()["output"]["choices"][0]["message"]["content"]
            # content 可能是 [{"text": "..."}] 列表, 也可能是纯字符串
            if isinstance(content, list):
                return "".join(seg.get("text", "") for seg in content)
            return str(content)

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        body = {
            "model": kwargs.get("model", self.image_model),
            "input": {"prompt": prompt},
            "parameters": {
                "size": kwargs.get("size", "1024*1024"),
                "n": 1,
            },
        }
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                f"{self.base_url}/services/aigc/text2image/image-synthesis",
                headers={**self._headers(), "X-DashScope-Async": "enable"},
                json=body,
            )
            r.raise_for_status()
            task_id = r.json()["output"]["task_id"]
            return await self._poll_task(client, task_id)

    async def _poll_task(
        self, client: httpx.AsyncClient, task_id: str
    ) -> str:
        url = f"{self.base_url}/tasks/{task_id}"
        for _ in range(60):  # 最多等 ~120s
            await asyncio.sleep(2)
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            data = r.json()["output"]
            status = data.get("task_status")
            if status == "SUCCEEDED":
                return data["results"][0]["url"]
            if status == "FAILED":
                raise RuntimeError(f"万相生图失败: {data}")
        raise TimeoutError("万相生图轮询超时")

    async def embed(self, image: str) -> list[float]:
        img = await resolve_image(image)
        body = {
            "model": self.embedding_model,
            "input": {"contents": [{"image": img["data_url"]}]},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.base_url}/services/embeddings/multimodal-embedding/multimodal-embedding",
                headers=self._headers(),
                json=body,
            )
            r.raise_for_status()
            return r.json()["output"]["embeddings"][0]["embedding"]

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
