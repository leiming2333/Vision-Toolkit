"""视觉 provider 抽象基类。

所有 provider 需实现:
  - analyze:  图像分析(描述/问答/OCR/检测的底层调用)
  - generate: 文生图
  - embed:    图像向量化(用于相似度对比), 默认抛 NotImplementedError,
              支持的 provider 覆盖此方法并将 supports_embedding 置 True。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VisionProvider(ABC):
    name: str = "base"
    supports_generation: bool = True
    supports_embedding: bool = False

    @abstractmethod
    async def analyze(self, image: str, prompt: str, **kwargs: Any) -> str:
        """用文本 prompt 分析图像, 返回模型的文本回复。

        image 为本地路径 / URL / data URL。
        """

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """根据文本 prompt 生成图像, 返回 data URL 或可访问的图像 URL。"""

    async def embed(self, image: str) -> list[float]:
        """返回图像的 embedding 向量。默认未实现。"""
        raise NotImplementedError(
            f"{self.name} 暂不支持图像 embedding, 请换用支持该能力的 provider。"
        )
