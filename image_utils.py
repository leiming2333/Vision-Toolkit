"""图像输入归一化工具。

将不同来源的图像引用(本地路径 / HTTP URL / data URL / 裸 base64)
统一解析为各 provider 都能消费的表示:data_url、base64、mime_type。
"""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import httpx


def _guess_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "image/jpeg"


async def _read_url(url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        mime = resp.headers.get("content-type", "").split(";")[0].strip()
        return resp.content, mime or _guess_mime(url)


def _read_file(path: str) -> tuple[bytes, str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"图像文件不存在: {path}")
    return p.read_bytes(), _guess_mime(path)


async def resolve_image(raw: str) -> dict:
    """把图像引用归一化为统一字典。

    支持的输入:
      - data URL:      data:image/png;base64,....
      - http(s) URL:   https://example.com/a.png
      - 本地文件路径:  C:\\imgs\\a.jpg  /  /tmp/a.jpg

    返回:
      {
        "source":    "data_url" | "url" | "file",
        "url":       原始 URL (若有, 否则空串),
        "data_url":  data:image/...;base64,...  (始终可用),
        "base64":    裸 base64 字符串 (无前缀),
        "mime_type": 例 "image/png",
      }
    """
    raw = raw.strip()

    # 1) data URL
    if raw.startswith("data:"):
        header, _, b64 = raw.partition(",")
        mime = "image/jpeg"
        if ":" in header:
            mime = header.split(":", 1)[1].split(";")[0] or mime
        return {
            "source": "data_url",
            "url": raw,
            "data_url": raw,
            "base64": b64,
            "mime_type": mime,
        }

    # 2) http(s) URL —— 下载后转 data_url, 以便 Gemini inline_data 等场景使用
    if raw.startswith("http://") or raw.startswith("https://"):
        try:
            data, mime = await _read_url(raw)
        except Exception:
            # 下载失败时直接把 URL 透传给 provider (部分 provider 会自行抓取)
            return {
                "source": "url",
                "url": raw,
                "data_url": raw,
                "base64": "",
                "mime_type": _guess_mime(raw),
            }
        b64 = base64.b64encode(data).decode()
        return {
            "source": "url",
            "url": raw,
            "data_url": f"data:{mime};base64,{b64}",
            "base64": b64,
            "mime_type": mime,
        }

    # 3) 本地文件
    data, mime = _read_file(raw)
    b64 = base64.b64encode(data).decode()
    return {
        "source": "file",
        "url": "",
        "data_url": f"data:{mime};base64,{b64}",
        "base64": b64,
        "mime_type": mime,
    }
