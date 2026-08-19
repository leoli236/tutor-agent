"""
统一的 LLM 调用封装

支持智谱 GLM 系列模型，提供文本对话和图片理解两种调用方式。
如果你使用其他 API（如 OpenAI、DeepSeek），只需修改本文件即可。
"""

import base64
import json
import os
import httpx

from config import (ZHIPU_API_KEY, VISION_MODEL, TEXT_MODEL, LLM_BASE_URL,
                    LLM_PROVIDER, OPENROUTER_HTTP_REFERER, OPENROUTER_APP_TITLE)

BASE_URL = LLM_BASE_URL
TIMEOUT = 60


def _call_api(model, messages, temperature=0.7, max_tokens=2048, response_format=None):
    """底层 API 调用"""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    if not ZHIPU_API_KEY or ZHIPU_API_KEY == "your_api_key_here":
        raise RuntimeError("未配置大模型 API Key，请在 Streamlit Secrets 中设置 OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json",
    }
    if LLM_PROVIDER.lower() == "openrouter":
        if OPENROUTER_HTTP_REFERER:
            headers["HTTP-Referer"] = OPENROUTER_HTTP_REFERER
        headers["X-Title"] = OPENROUTER_APP_TITLE

    resp = httpx.post(BASE_URL, headers=headers, json=payload, timeout=TIMEOUT)
    if resp.status_code == 400 and response_format:
        payload.pop("response_format", None)
        resp = httpx.post(BASE_URL, headers=headers, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def chat_text(system_prompt: str, user_message: str,
              temperature=0.7, max_tokens=2048) -> str:
    """
    纯文本对话
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return _call_api(TEXT_MODEL, messages, temperature=temperature, max_tokens=max_tokens)


def chat_text_json(system_prompt: str, user_message: str,
                   temperature=0.3, max_tokens=4096) -> dict:
    """
    文本对话，强制返回 JSON 格式
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    raw = _call_api(
        TEXT_MODEL, messages,
        temperature=temperature, max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    return json.loads(raw)


def chat_vision(system_prompt: str, image_path: str,
                user_text: str = "") -> str:
    """
    图片理解对话：发送图片 + 文字，返回模型回复
    """
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    user_content = []
    if image_path:
        suffix = os.path.splitext(image_path)[1].lower()
        mime = {"jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".webp": "image/webp"}.get(suffix, "image/jpeg")
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"},
        })
    if user_text:
        user_content.append({"type": "text", "text": user_text})

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    return _call_api(VISION_MODEL, messages, temperature=0.3, max_tokens=2048)


def chat_vision_json(system_prompt: str, image_path: str,
                     user_text: str = "") -> dict:
    """
    图片理解对话，强制返回 JSON
    """
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    user_content = []
    suffix = os.path.splitext(image_path)[1].lower()
    mime = {"jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp"}.get(suffix, "image/jpeg")
    user_content.append({
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{b64}"},
    })
    if user_text:
        user_content.append({"type": "text", "text": user_text})

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    raw = _call_api(
        VISION_MODEL, messages,
        temperature=0.3, max_tokens=4096,
        response_format={"type": "json_object"},
    )
    return json.loads(raw)
