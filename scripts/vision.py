"""独立视觉理解脚本 —— 可被任意 agent / skill 直接调用,不依赖 MCP server。

用法:
    python vision.py analyze --image cat.jpg --prompt "图里有几只猫?"
    python vision.py ocr --image doc.png --language zh
    python vision.py detect --image street.jpg
    python vision.py compare --image1 a.png --image2 b.png

环境变量(至少配置一个 provider 的 Key),与 server.py 共用:
    OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_VISION_MODEL
    DASHSCOPE_API_KEY / QWEN_VL_MODEL
    GEMINI_API_KEY / GEMINI_VISION_MODEL

输出: 打印模型的文本回复(analyze/ocr/detect)或相似度分数(compare)。

调用失败时自动降级:若指定 provider 调用出错,会依次尝试其他已配置的
provider,直到有一个成功或全部失败(与 scripts/generate_image.py 行为一致)。
"""
from __future__ import annotations

import argparse
import asyncio
import math
import os
import sys

# 让脚本无论从哪里调用都能 import 同级 providers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers import PROVIDER_CLASSES, VisionProvider  # noqa: E402


def _init_providers() -> dict[str, VisionProvider]:
    providers: dict[str, VisionProvider] = {}
    for key, cls in PROVIDER_CLASSES.items():
        try:
            providers[key] = cls()
        except RuntimeError:
            # 该 provider 缺少 API Key, 静默跳过
            pass
    return providers


def _candidate_order(
    providers: dict[str, VisionProvider],
    provider_name: str | None,
    *,
    embedding_only: bool = False,
) -> list[str]:
    """候选 provider 顺序: 指定的优先, 其余已配置的作为降级备选。

    embedding_only=True 时只保留支持原生 embedding 的 provider (用于 compare 的首选)。
    """
    pool = {
        k: v for k, v in providers.items()
        if (not embedding_only or v.supports_embedding)
    }
    if not pool:
        return []
    if provider_name and provider_name in pool:
        return [provider_name] + [k for k in pool if k != provider_name]
    return list(pool.keys())


async def _run_analyze_with_fallback(
    providers: dict[str, VisionProvider],
    provider_name: str | None,
    image: str,
    prompt: str,
) -> str:
    """依次尝试候选 provider 调用 analyze, 成功即返回文本结果。

    指定 provider 调用出错时, 自动降级到其余已配置的 provider。
    """
    order = _candidate_order(providers, provider_name)
    if not order:
        raise RuntimeError(
            "未配置任何 provider, 请至少设置一个 API Key: "
            "OPENAI_API_KEY / DASHSCOPE_API_KEY / GEMINI_API_KEY"
        )
    last_err: Exception | None = None
    tried: list[str] = []
    for name in order:
        try:
            return await providers[name].analyze(image, prompt)
        except Exception as e:  # noqa: BLE001
            tried.append(f"{name}({type(e).__name__}: {e})")
            last_err = e
            continue
    raise RuntimeError(
        "所有 provider 调用均失败, 已尝试: " + "; ".join(tried)
        + f"。最后错误: {last_err}"
    )


async def _run_compare_with_fallback(
    providers: dict[str, VisionProvider],
    provider_name: str | None,
    image1: str,
    image2: str,
) -> str:
    """对比两张图像相似度, 带 provider 自动降级。

    优先使用支持原生多模态 embedding 的 provider (如 qwen); 若无或失败,
    回退到其余 provider 的「描述 + 文本 embedding」兜底策略。
    """
    # 首选: 原生 embedding provider; 失败再回退到全部 provider (含描述兜底)
    native_order = _candidate_order(providers, provider_name, embedding_only=True)
    all_order = _candidate_order(providers, provider_name)
    order = native_order + [n for n in all_order if n not in native_order]
    if not order:
        raise RuntimeError(
            "未配置任何 provider, 请至少设置一个 API Key: "
            "OPENAI_API_KEY / DASHSCOPE_API_KEY / GEMINI_API_KEY"
        )
    last_err: Exception | None = None
    tried: list[str] = []
    for name in order:
        p = providers[name]
        try:
            e1, e2 = await asyncio.gather(p.embed(image1), p.embed(image2))
        except Exception as e:  # noqa: BLE001
            tried.append(f"{name}({type(e).__name__}: {e})")
            last_err = e
            continue
        score = _cosine(e1, e2)
        return (
            f"相似度: {score:.3f}\n"
            f"(0.0 = 完全不同, 1.0 = 完全相同)\n"
            f"embedding provider: {name}"
        )
    raise RuntimeError(
        "所有 provider 对比均失败, 已尝试: " + "; ".join(tried)
        + f"。最后错误: {last_err}"
    )


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Vision Toolkit 独立视觉理解脚本")
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="图像描述 / 视觉问答")
    p_analyze.add_argument("--image", required=True, help="图像引用(路径 / URL / data URL)")
    p_analyze.add_argument("--prompt", help="对图像的提问或指令, 省略则描述图片")
    p_analyze.add_argument("--provider", choices=["openai", "qwen", "gemini"])

    p_ocr = sub.add_parser("ocr", help="提取图中文字")
    p_ocr.add_argument("--image", required=True, help="图像引用(路径 / URL / data URL)")
    p_ocr.add_argument("--language", help="语言提示, 如 zh / en / ja")
    p_ocr.add_argument("--provider", choices=["openai", "qwen", "gemini"])

    p_detect = sub.add_parser("detect", help="物体检测(标签 + 置信度 + 九宫格位置)")
    p_detect.add_argument("--image", required=True, help="图像引用(路径 / URL / data URL)")
    p_detect.add_argument("--provider", choices=["openai", "qwen", "gemini"])

    p_compare = sub.add_parser("compare", help="图像相似度对比(余弦相似度 0~1)")
    p_compare.add_argument("--image1", required=True, help="第一张图像(路径 / URL / data URL)")
    p_compare.add_argument("--image2", required=True, help="第二张图像(路径 / URL / data URL)")
    p_compare.add_argument("--provider", choices=["openai", "qwen", "gemini"])

    args = parser.parse_args()

    providers = _init_providers()
    if not providers:
        print(
            "ERROR: 未配置任何 provider, 请至少设置一个 API Key: "
            "OPENAI_API_KEY / DASHSCOPE_API_KEY / GEMINI_API_KEY",
            file=sys.stderr,
        )
        return 1

    try:
        if args.command == "analyze":
            prompt = args.prompt or "请详细描述这张图片。"
            result = await _run_analyze_with_fallback(
                providers, args.provider, args.image, prompt
            )
        elif args.command == "ocr":
            prompt = "请提取并原样返回图中所有可见文字, 保留换行。"
            if args.language:
                prompt += f" 文字主要为 {args.language}。"
            prompt += " 只返回提取到的文字本身。"
            result = await _run_analyze_with_fallback(
                providers, args.provider, args.image, prompt
            )
        elif args.command == "detect":
            prompt = (
                "检测图中主要物体, 每个物体输出一行, 格式: label (置信度%) - 位置。\n"
                "位置取值: top-left, top-center, top-right, center-left, center, "
                "center-right, bottom-left, bottom-center, bottom-right。\n"
                "示例:\n"
                "person (92%) - center-left\n"
                "car (88%) - bottom-right"
            )
            result = await _run_analyze_with_fallback(
                providers, args.provider, args.image, prompt
            )
        elif args.command == "compare":
            result = await _run_compare_with_fallback(
                providers, args.provider, args.image1, args.image2
            )
        else:  # argparse 已保证 command 合法, 此处不会到达
            parser.error(f"未知命令: {args.command}")
            return 2
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
