"""
配置文件 —— API Key 自动从三个来源读取（优先级从高到低）

1. Streamlit Secrets（云端部署时在 .streamlit/secrets.toml 中配置）
2. 环境变量 ZHIPU_API_KEY（Docker / 本地设置）
3. 本地 config.py 中的 FALLBACK_KEY（个人本地开发用）
"""

import os


def _load_secret(*names):
    for name in names:
        try:
            import streamlit as st
            value = st.secrets.get(name, "")
            if value:
                return value
        except Exception:
            pass
        value = os.environ.get(name, "")
        if value:
            return value
    return ""


def _load_api_key():
    """三级 fallback 读取 API Key"""
    # 1. Streamlit Cloud secrets
    try:
        import streamlit as st
        key = st.secrets.get("LLM_API_KEY", "") or st.secrets.get("OPENROUTER_API_KEY", "") or st.secrets.get("ZHIPU_API_KEY", "")
        if key and key != "your_api_key_here":
            return key
    except Exception:
        pass
    # 2. 环境变量
    key = os.environ.get("LLM_API_KEY", "") or os.environ.get("OPENROUTER_API_KEY", "") or os.environ.get("ZHIPU_API_KEY", "")
    if key:
        return key
    # 3. 本地 fallback
    return FALLBACK_KEY


# ── 如果你只在本地用，直接改这里就行 ──
FALLBACK_KEY = "your_api_key_here"

ZHIPU_API_KEY = _load_api_key()
LLM_PROVIDER = _load_secret("LLM_PROVIDER") or "openrouter"
LLM_BASE_URL = _load_secret("LLM_BASE_URL") or "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_HTTP_REFERER = _load_secret("OPENROUTER_HTTP_REFERER")
OPENROUTER_APP_TITLE = _load_secret("OPENROUTER_APP_TITLE") or "AI Tutor Workbench"

# 模型配置
VISION_MODEL = _load_secret("VISION_MODEL") or "nvidia/nemotron-nano-12b-v2-vl:free"
TEXT_MODEL = _load_secret("TEXT_MODEL") or "google/gemma-4-31b-it:free"

# 数据库路径（云端自动用 /mount/src/data）
if os.path.exists("/mount/src"):
    _DATA_DIR = "/mount/src/data"
else:
    _DATA_DIR = "data"
DB_PATH = os.path.join(_DATA_DIR, "tutor.db")
UPLOAD_DIR = os.path.join(_DATA_DIR, "uploads")

# 学科列表
SUBJECTS = ["数学", "英语", "Python编程"]

# 错误类型
ERROR_TYPES = [
    "知识性错误",
    "审题不清",
    "计算粗心",
    "书写/格式错误",
    "逻辑混乱",
    "其他",
]

# 年级列表
GRADES = [
    "小学一年级", "小学二年级", "小学三年级", "小学四年级",
    "小学五年级", "小学六年级", "初一", "初二", "初三",
    "高一", "高二", "高三",
]
