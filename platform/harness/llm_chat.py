"""Unified chat+tools client for Azure OpenAI-compatible and Anthropic Messages API."""
from __future__ import annotations

import json
import os
from typing import Any

from azure_models import MODELS, chat_temperature_kwargs, chat_token_kwargs

# Claude via official Anthropic API (not Azure Foundry)
CLAUDE_MODEL_ID = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
MODELS_EXTRA = {
    "claude": (CLAUDE_MODEL_ID, "anthropic"),
}
# Merge into usable registry without mutating import-time Azure dict unexpectedly
ALL_MODELS = {**MODELS, **MODELS_EXTRA}


def resolve_model(model_key: str) -> tuple[str, str, str]:
    """Return (provider, model_name, base_url_or_sentinel). provider: azure|anthropic"""
    if model_key == "claude" or model_key not in MODELS:
        name, kind = MODELS_EXTRA.get(model_key, MODELS.get(model_key, (model_key, "azure")))
        if kind == "anthropic" or model_key == "claude":
            return "anthropic", CLAUDE_MODEL_ID, "anthropic"
    name, url = MODELS[model_key]
    return "azure", name, url


def _openai_tools_to_anthropic(tools: list[dict]) -> list[dict]:
    out = []
    for t in tools:
        fn = t.get("function") or {}
        out.append({
            "name": fn["name"],
            "description": fn.get("description") or "",
            "input_schema": fn.get("parameters") or {"type": "object", "properties": {}},
        })
    return out


def _anthropic_key() -> str:
    # Prefer env; callers may inject via vault wrapper
    k = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
    if not k:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Store it: ~/.llm-vault/hooks/vault store ANTHROPIC_API_KEY"
        )
    return k


def chat_tools(
    *,
    model_key: str,
    messages: list[dict],
    tools: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """One tool-loop step. Returns OpenAI-shaped message dict + usage.

    Output:
      {
        "message": {role, content, tool_calls?: [{id, function:{name, arguments}}], reasoning?},
        "usage": {"in": int, "out": int},
        "raw_provider": "azure"|"anthropic",
      }
    """
    provider, model_name, base = resolve_model(model_key)

    if provider == "anthropic":
        return _chat_anthropic(model_name, messages, tools, max_tokens=max_tokens)

    from openai import OpenAI
    client = OpenAI(api_key=os.environ["AZURE_OPENAI_API_KEY"], base_url=base)
    kwargs = dict(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        **chat_temperature_kwargs(model_key, temperature),
        **chat_token_kwargs(model_key, model_name, n=max_tokens),
    )
    r = client.chat.completions.create(**kwargs)
    m = r.choices[0].message
    usage = {"in": 0, "out": 0}
    if r.usage:
        usage["in"] = getattr(r.usage, "prompt_tokens", 0) or 0
        usage["out"] = getattr(r.usage, "completion_tokens", 0) or 0
    msg = m.model_dump(exclude_none=True)
    # normalize tool_calls to plain dicts
    return {"message": msg, "usage": usage, "raw_provider": "azure"}


def _split_system(messages: list[dict]) -> tuple[str | None, list[dict]]:
    system = None
    rest = []
    for m in messages:
        role = m.get("role")
        if role == "system" and system is None:
            system = m.get("content") or ""
        else:
            rest.append(m)
    return system, rest


def _to_anthropic_messages(messages: list[dict]) -> list[dict]:
    """Convert OpenAI-style history (with tool roles) to Anthropic messages."""
    system, rest = _split_system(messages)
    out: list[dict] = []
    i = 0
    while i < len(rest):
        m = rest[i]
        role = m.get("role")
        if role == "assistant":
            content_blocks = []
            if m.get("content"):
                content_blocks.append({"type": "text", "text": m["content"]})
            for tc in m.get("tool_calls") or []:
                # tc may be dict from model_dump
                if isinstance(tc, dict):
                    fn = tc.get("function") or {}
                    tid = tc.get("id") or "tool"
                    args = fn.get("arguments") or "{}"
                    if isinstance(args, str):
                        try:
                            args_obj = json.loads(args)
                        except Exception:
                            args_obj = {"raw": args}
                    else:
                        args_obj = args
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tid,
                        "name": fn.get("name") or "bash",
                        "input": args_obj,
                    })
            out.append({"role": "assistant", "content": content_blocks or [{"type": "text", "text": ""}]})
            i += 1
        elif role == "user":
            out.append({"role": "user", "content": m.get("content") or ""})
            i += 1
        elif role == "tool":
            # gather consecutive tool results into one user message
            blocks = []
            while i < len(rest) and rest[i].get("role") == "tool":
                tm = rest[i]
                blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tm.get("tool_call_id") or "tool",
                    "content": tm.get("content") or "",
                })
                i += 1
            out.append({"role": "user", "content": blocks})
        else:
            # skip unknown
            i += 1
    return out


def _chat_anthropic(model_name: str, messages: list[dict], tools: list[dict], max_tokens: int) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=_anthropic_key())
    system, _ = _split_system(messages)
    a_msgs = _to_anthropic_messages(messages)
    kwargs: dict[str, Any] = {
        "model": model_name,
        "max_tokens": max_tokens,
        "messages": a_msgs,
        "tools": _openai_tools_to_anthropic(tools),
    }
    if system:
        kwargs["system"] = system
    r = client.messages.create(**kwargs)
    text_parts = []
    tool_calls = []
    for block in r.content:
        btype = getattr(block, "type", None)
        if btype == "text":
            text_parts.append(block.text)
        elif btype == "tool_use":
            tool_calls.append({
                "id": block.id,
                "type": "function",
                "function": {
                    "name": block.name,
                    "arguments": json.dumps(block.input or {}),
                },
            })
    msg: dict[str, Any] = {"role": "assistant", "content": "\n".join(text_parts) or None}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    usage = {
        "in": getattr(r.usage, "input_tokens", 0) or 0,
        "out": getattr(r.usage, "output_tokens", 0) or 0,
    }
    return {"message": msg, "usage": usage, "raw_provider": "anthropic"}
