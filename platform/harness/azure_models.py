"""Shared Azure model registry for score-seeking task runners."""
from __future__ import annotations

import os

_RES = os.environ.get("AZURE_AI_RESOURCE", "your-ai-services-resource")
_FOUNDRY = f"https://{_RES}.services.ai.azure.com/openai/v1"

# model_key -> (deployment_name, base_url)
MODELS: dict[str, tuple[str, str]] = {
    "deepseek": ("DeepSeek-V4-Pro", _FOUNDRY),
    "kimi": ("Kimi-K2.6", _FOUNDRY),
    "gpt-4o": ("gpt-4o", _FOUNDRY),
    "gpt-5.4": ("gpt-5.4", _FOUNDRY),  # OpenAI frontier stand-in for reasoning panel slot
    # Anthropic direct API (not Azure). Sentinel base_url; see llm_chat.py.
    "claude": (os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"), "anthropic"),
}

# Map runner model_key -> propensity_schema MODEL_META key
PROPENSITY_MODEL_KEY = {
    "deepseek": "deepseek",
    "kimi": "kimi",
    "gpt-4o": "gpt-4o",
    "gpt-5.4": "openai-reasoning",
    "o3": "openai-reasoning",
    "qwen": "qwen",
    "claude": "claude",
}

# Models that reject chat.completions `max_tokens` (need max_completion_tokens).
_MAX_COMPLETION_MODELS = ("gpt-5.4", "gpt-5.4-mini", "o3", "o4-mini")


def chat_token_kwargs(model_key: str, model_name: str | None = None, n: int = 2048) -> dict[str, int]:
    """Kwargs for chat.completions.create token limit (Azure model-family quirks)."""
    name = model_name or MODELS.get(model_key, (model_key,))[0]
    if model_key in _MAX_COMPLETION_MODELS or str(name).startswith(("gpt-5", "o3", "o4")):
        return {"max_completion_tokens": n}
    return {"max_tokens": n}


def chat_temperature_kwargs(model_key: str, temperature: float = 0.2) -> dict[str, float]:
    """Some reasoning deployments reject non-default temperature; omit when needed."""
    if model_key in _MAX_COMPLETION_MODELS or model_key.startswith("gpt-5"):
        return {}  # let API default
    return {"temperature": temperature}

# Deploy status (2026-09-19, westus3 AIServices yilongjack2001-6481-resource):
# - gpt-5.4: deployed (OpenAI reasoning panel stand-in)
# - qwen3-32b: catalog lists Alibaba/GlobalStandard but deployment rejected (SKU not supported on this account)
# - claude-sonnet-*: requires ModelProviderData (industry/org/country); ARM PUT still rejected — use portal/ToS acceptance
