"""
LLM 客户端工厂 — 根据配置创建对应的 Provider 实例

优先读取新配置 (LLM_*), 兼容旧配置 (MINIMAX_*)
切换 Provider 只需改 .env, 无需改代码。

.env 配置示例:
    # MiniMax 云端
    LLM_BASE_URL=https://api.minimaxi.com/v1
    LLM_API_KEY=your-minimax-key
    LLM_MODEL=MiniMax-M2.7

    # Ollama 本地
    LLM_BASE_URL=http://localhost:11434/v1
    LLM_API_KEY=
    LLM_MODEL=qwen2.5:14b

    # vLLM 本地
    LLM_BASE_URL=http://localhost:8000/v1
    LLM_API_KEY=token-abc123
    LLM_MODEL=Qwen/Qwen2.5-14B-Instruct
"""
import logging
import os

from app.llm.base import LLMProvider
from app.llm.providers.openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)

_instance: LLMProvider | None = None


def _resolve_config() -> dict[str, str]:
    """
    解析 LLM 配置，优先使用新 LLM_* 变量，回退到旧 MINIMAX_* 变量
    """
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    timeout = os.getenv("LLM_TIMEOUT_SECONDS", "").strip()
    max_input = os.getenv("LLM_MAX_INPUT_CHARS", "").strip()

    # 回退到旧配置
    if not base_url:
        base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1").strip()
    if not api_key:
        api_key = os.getenv("MINIMAX_API_KEY", "").strip()
    if not model:
        model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7").strip()
    if not timeout:
        timeout = os.getenv("MINIMAX_TIMEOUT_SECONDS", "60").strip()
    if not max_input:
        max_input = os.getenv("MINIMAX_MAX_INPUT_CHARS", "12000").strip()

    return {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "timeout_seconds": timeout,
        "max_input_chars": max_input,
    }


def get_llm_client() -> LLMProvider:
    """获取 LLM Provider 单例"""
    global _instance
    if _instance is not None:
        return _instance

    config = _resolve_config()
    logger.info(
        "Initializing LLM provider: base_url=%s, model=%s, api_key=%s",
        config["base_url"],
        config["model"],
        "***" if config["api_key"] else "<empty>",
    )

    _instance = OpenAICompatibleProvider(
        base_url=config["base_url"],
        api_key=config["api_key"],
        model=config["model"],
        timeout_seconds=float(config["timeout_seconds"]),
    )
    return _instance


def reset_llm_client() -> None:
    """重置单例（用于测试或动态切换配置）"""
    global _instance
    _instance = None
