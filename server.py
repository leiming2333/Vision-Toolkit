"""Vision Toolkit —— 多模态视觉 MCP + 文生图工具包。

暴露的工具:
  - list_providers    : 列出已配置的 provider 及能力
  - analyze_image     : 图像描述 / 问答
  - ocr               : OCR 文字识别
  - detect_objects    : 物体检测(标签 + 置信度 + 大致位置)
  - generate_image    : 文生图
  - compare_images    : 图像相似度对比(余弦相似度)

环境变量(至少配置一个 provider 的 Key),详见 .env.example:
  OPENAI_API_KEY / DASHSCOPE_API_KEY / GEMINI_API_KEY / ANTHROPIC_API_KEY

传输方式:
  stdio (默认):  python server.py
  SSE:           python server.py --transport sse --host 0.0.0.0 --port 8765
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

# 允许从任意 cwd 启动时仍能 import 同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from providers import PROVIDER_CLASSES, VisionProvider  # noqa: E402


# ---------------------------------------------------------------------------
# .env 加载: 启动时自动读取 ~/.vision-toolkit.env 和包目录 .env
# ---------------------------------------------------------------------------
def _load_env_file(path: str) -> None:
    """手动解析 .env 文件, 设置 os.environ (不覆盖已有值)。"""
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                eq = line.find("=")
                if eq == -1:
                    continue
                key = line[:eq].strip()
                val = line[eq + 1:].strip()
                # 去引号
                if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
                    val = val[1:-1]
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass  # .env 解析失败不阻断启动


def _load_envs() -> None:
    """加载 .env, 优先级: 系统环境变量 > 包目录 .env > ~/.vision-toolkit.env"""
    home_env = os.path.join(os.path.expanduser("~"), ".vision-toolkit.env")
    _load_env_file(home_env)
    pkg_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    _load_env_file(pkg_env)


_load_envs()


# ---------------------------------------------------------------------------
# MODID 自动获取: 模型未配置时, 通过 API 获取可用模型列表
# ---------------------------------------------------------------------------
def _auto_detect_models() -> None:
    """如果 vision/image model 为空, 尝试通过 API 自动获取。

    仅支持 OpenAI 兼容端点 (GET {base_url}/models)。
    其他 provider 静默跳过。
    """
    import httpx

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return

    # 视觉模型未配置时尝试获取
    if not os.environ.get("OPENAI_VISION_MODEL"):
        try:
            r = httpx.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            r.raise_for_status()
            models = r.json().get("data", [])
            # 优先选含 gpt-4 的, 否则取第一个
            vision = next(
                (m["id"] for m in models if "gpt-4" in m.get("id", "")),
                models[0]["id"] if models else "",
            )
            if vision:
                os.environ["OPENAI_VISION_MODEL"] = vision
                print(f"[vision-toolkit] 自动获取视觉模型: {vision}", file=sys.stderr)
        except Exception:
            pass  # 获取失败使用 provider 默认值

    # 生图模型未配置时用默认值
    if not os.environ.get("OPENAI_IMAGE_MODEL"):
        os.environ.setdefault("OPENAI_IMAGE_MODEL", "dall-e-3")


_auto_detect_models()


# ---------------------------------------------------------------------------
# Provider 注册表: 启动时按可用 API Key 自动装载
# ---------------------------------------------------------------------------
_providers: dict[str, VisionProvider] = {}


def _init_providers() -> None:
    for key, cls in PROVIDER_CLASSES.items():
        try:
            _providers[key] = cls()
        except RuntimeError:
            # 该 provider 缺少 API Key, 静默跳过
            pass


def _get_provider(name: str | None) -> VisionProvider:
    if not _providers:
        raise RuntimeError(
            "未配置任何视觉 provider, 请至少设置一个 API Key: "
            "OPENAI_API_KEY / DASHSCOPE_API_KEY / GEMINI_API_KEY / ANTHROPIC_API_KEY"
        )
    if name:
        if name not in _providers:
            raise ValueError(
                f"provider '{name}' 未配置, 可用: {list(_providers)}"
            )
        return _providers[name]
    # 默认取第一个已配置的 provider
    return next(iter(_providers.values()))


_init_providers()

mcp = FastMCP("vision-toolkit")


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------
@mcp.tool()
async def list_providers() -> str:
    """列出当前可用的视觉 provider 及其能力。"""
    if not _providers:
        return (
            "未配置任何 provider。请设置 OPENAI_API_KEY、DASHSCOPE_API_KEY "
            "或 GEMINI_API_KEY 后重启服务。"
        )
    lines = ["已配置的 provider:"]
    for name, p in _providers.items():
        caps = ["vision"]
        if p.supports_generation:
            caps.append("image-generation")
        if p.supports_embedding:
            caps.append("embedding")
        lines.append(f"  - {name}: {', '.join(caps)}")
    lines.append(f"\n默认 provider: {next(iter(_providers))}")
    return "\n".join(lines)


@mcp.tool()
async def analyze_image(
    image: str,
    prompt: str = "请详细描述这张图片。",
    provider: str | None = None,
) -> str:
    """用文本 prompt 分析图像(图像描述 / 视觉问答)。

    Args:
        image: 图像引用 —— 本地路径 / http(s) URL / data:image/...;base64,... 数据 URL。
        prompt: 对图像的提问或指令。
        provider: 指定 provider (openai / qwen / gemini), 省略则用默认。
    """
    p = _get_provider(provider)
    return await p.analyze(image, prompt)


@mcp.tool()
async def ocr(
    image: str,
    language: str = "",
    provider: str | None = None,
) -> str:
    """从图像中提取文字 (OCR)。

    Args:
        image: 图像引用(路径 / URL / data URL)。
        language: 可选语言提示, 如 "zh"、"en"、"ja"。
        provider: 指定 provider, 省略则用默认。
    """
    p = _get_provider(provider)
    prompt = "请提取并原样返回图中所有可见文字, 保留换行。"
    if language:
        prompt += f" 文字主要为 {language}。"
    prompt += " 只返回提取到的文字本身。"
    return await p.analyze(image, prompt)


@mcp.tool()
async def detect_objects(
    image: str,
    provider: str | None = None,
) -> str:
    """检测图像中的主要物体, 返回标签、置信度与大致位置。

    位置使用九宫格描述: top-left / top-center / top-right /
    center-left / center / center-right / bottom-left / bottom-center / bottom-right。

    Args:
        image: 图像引用(路径 / URL / data URL)。
        provider: 指定 provider, 省略则用默认。
    """
    p = _get_provider(provider)
    prompt = (
        "检测图中主要物体, 每个物体输出一行, 格式: label (置信度%) - 位置。\n"
        "位置取值: top-left, top-center, top-right, center-left, center, "
        "center-right, bottom-left, bottom-center, bottom-right。\n"
        "示例:\n"
        "person (92%) - center-left\n"
        "car (88%) - bottom-right"
    )
    return await p.analyze(image, prompt)


@mcp.tool()
async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    provider: str | None = None,
) -> str:
    """根据文本 prompt 生成图像, 返回 data URL。

    生图失败时自动降级:若指定 provider 调用出错,会依次尝试其他已配置的
    provider,直到有一个成功或全部失败。

    Args:
        prompt: 想要生成的图像描述。
        size: 图像尺寸。OpenAI/Gemini 用 WxH (如 1024x1024);
              Qwen 用 W*H (如 1024*1024), 也可传 WxH 会自动转换。
        provider: 指定 provider, 省略则用默认; 指定失败会自动降级到其他。
    """
    if not _providers:
        raise RuntimeError(
            "未配置任何视觉 provider, 请至少设置一个 API Key: "
            "OPENAI_API_KEY / DASHSCOPE_API_KEY / GEMINI_API_KEY / ANTHROPIC_API_KEY"
        )
    # 候选顺序: 指定的优先, 其余已配置的作为降级备选
    if provider:
        if provider not in _providers:
            raise ValueError(
                f"provider '{provider}' 未配置, 可用: {list(_providers)}"
            )
        order = [provider] + [k for k in _providers if k != provider]
    else:
        order = list(_providers.keys())

    last_err: Exception | None = None
    tried: list[str] = []
    for name in order:
        p = _providers[name]
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


@mcp.tool()
async def compare_images(
    image1: str,
    image2: str,
    provider: str | None = None,
) -> str:
    """对比两张图像的相似度, 返回 0.0~1.0 的余弦相似度。

    Qwen 使用原生多模态图像 embedding(按图像内容向量化);
    OpenAI/Gemini 采用「先描述再文本 embedding」的兜底策略;
    Anthropic Claude 不支持 embedding, 会自动降级到其他 provider。

    Args:
        image1: 第一张图像(路径 / URL / data URL)。
        image2: 第二张图像(路径 / URL / data URL)。
        provider: 指定用于 embedding 的 provider, 省略则用默认。
    """
    p = _get_provider(provider)
    # 若所选 provider 不支持 embedding, 回退到任意支持的 provider
    if not p.supports_embedding:
        p = next(
            (c for c in _providers.values() if c.supports_embedding), p
        )
    e1, e2 = await asyncio.gather(p.embed(image1), p.embed(image2))
    score = _cosine(e1, e2)
    return (
        f"相似度: {score:.3f}\n"
        f"(0.0 = 完全不同, 1.0 = 完全相同)\n"
        f"embedding provider: {p.name}"
    )


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Vision Toolkit")
    parser.add_argument(
        "--transport", choices=["stdio", "sse"], default="stdio",
        help="传输方式: stdio (默认) 或 sse",
    )
    parser.add_argument("--host", default="127.0.0.1", help="SSE 监听地址")
    parser.add_argument("--port", type=int, default=8765, help="SSE 监听端口")
    args = parser.parse_args()

    if args.transport == "sse":
        # 官方 mcp SDK 通过 settings 读取 host/port
        try:
            mcp.settings.host = args.host
            mcp.settings.port = args.port
        except Exception:
            # 某些版本 settings 不可写时退回环境变量
            os.environ.setdefault("FASTMCP_HOST", args.host)
            os.environ.setdefault("FASTMCP_PORT", str(args.port))
        mcp.run(transport="sse")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
