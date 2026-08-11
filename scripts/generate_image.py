"""独立文生图脚本 —— 可被任意 agent / skill 直接调用,不依赖 MCP server。

用法:
    python generate_image.py --prompt "赛博朋克猫咪" --provider qwen
    python generate_image.py --prompt "a cat" --provider openai --size 1024x1024
    python generate_image.py --prompt "a cat" --provider gemini --out out.png

环境变量(至少配置一个 provider 的 Key),与 server.py 共用:
    OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_IMAGE_MODEL
    DASHSCOPE_API_KEY / QWEN_IMAGE_MODEL
    GEMINI_API_KEY / GEMINI_IMAGE_MODEL

输出:
    默认把生成的图像(data URL 或远程 URL)保存为本地 PNG 文件并打印路径。
    可用 --data-url 只打印 data URL 不落盘。
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import os
import re
import sys

# 让脚本无论从哪里调用都能 import 同级 providers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx  # noqa: E402

from providers import PROVIDER_CLASSES, VisionProvider  # noqa: E402


def _init_providers() -> dict[str, VisionProvider]:
    providers: dict[str, VisionProvider] = {}
    for key, cls in PROVIDER_CLASSES.items():
        try:
            providers[key] = cls()
        except RuntimeError:
            pass
    return providers


async def generate(provider_name: str, prompt: str, size: str) -> str:
    """调用指定 provider 生成图像, 返回 data URL。

    生图失败时自动降级:若指定 provider 调用出错,会依次尝试其他已配置的
    provider,直到有一个成功或全部失败。
    """
    providers = _init_providers()
    if not providers:
        raise RuntimeError(
            "未配置任何 provider, 请至少设置一个 API Key: "
            "OPENAI_API_KEY / DASHSCOPE_API_KEY / GEMINI_API_KEY"
        )
    # 候选顺序: 指定的优先, 其余已配置的作为降级备选
    if provider_name not in providers:
        # 指定的未配置时, 直接降级到其余已配置的 provider
        order = list(providers.keys())
    else:
        order = [provider_name] + [k for k in providers if k != provider_name]

    last_err: Exception | None = None
    tried: list[str] = []
    for name in order:
        p = providers[name]
        # Qwen 万相的 size 分隔符是 '*'
        qwen_size = size.replace("x", "*") if p.name == "qwen" else size
        try:
            return await p.generate(prompt, size=qwen_size)
        except Exception as e:  # noqa: BLE001
            tried.append(f"{name}({type(e).__name__}: {e})")
            last_err = e
            continue
    raise RuntimeError(
        "所有 provider 生图均失败, 已尝试: " + "; ".join(tried)
        + f"。最后错误: {last_err}"
    )


def _save_png(data_url: str, out_path: str) -> str:
    """把 data URL 或 http URL 保存为本地 PNG 文件, 返回绝对路径。"""
    if data_url.startswith("data:"):
        m = re.match(r"data:image/\w+;base64,(.+)", data_url, re.S)
        if not m:
            raise ValueError("无法解析 data URL")
        data = base64.b64decode(m.group(1))
    else:
        # 远程 URL (如万相返回的) —— 下载
        r = httpx.get(data_url, timeout=120, follow_redirects=True)
        r.raise_for_status()
        data = r.content
    if not out_path.endswith(".png"):
        out_path += ".png"
    with open(out_path, "wb") as f:
        f.write(data)
    return os.path.abspath(out_path)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Vision Toolkit 独立文生图脚本")
    parser.add_argument("--prompt", "-p", required=True, help="图像描述")
    parser.add_argument(
        "--provider", default="openai",
        choices=["openai", "qwen", "gemini"],
        help="生图 provider, 默认 openai",
    )
    parser.add_argument("--size", default="1024x1024", help="图像尺寸, 默认 1024x1024")
    parser.add_argument("--out", "-o", default="generated.png", help="输出文件路径")
    parser.add_argument(
        "--data-url", action="store_true",
        help="只打印 data URL, 不保存文件",
    )
    args = parser.parse_args()

    try:
        data_url = await generate(args.provider, args.prompt, args.size)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.data_url:
        print(data_url)
    else:
        path = _save_png(data_url, args.out)
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
