"""
配置文件 —— API Key 自动从三个来源读取（优先级从高到低）

1. Streamlit Secrets（云端部署时在 .streamlit/secrets.toml 中配置）
2. 环境变量 ZHIPU_API_KEY（Docker / 本地设置）
3. 本地 config.py 中的 FALLBACK_KEY（个人本地开发用）
"""

import os


def _load_api_key():
    """三级 fallback 读取 API Key"""
    # 1. Streamlit Cloud secrets
    try:
        import streamlit as st
        key = st.secrets.get("ZHIPU_API_KEY", "")
        if key and key != "your_api_key_here":
            return key
    except Exception:
        pass
    # 2. 环境变量
    key = os.environ.get("ZHIPU_API_KEY", "")
    if key:
        return key
    # 3. 本地 fallback
    return FALLBACK_KEY


# ── 如果你只在本地用，直接改这里就行 ──
FALLBACK_KEY = "your_api_key_here"

ZHIPU_API_KEY = _load_api_key()

# 模型配置
VISION_MODEL = "glm-4v-flash"
TEXT_MODEL = "glm-4-flash"

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
