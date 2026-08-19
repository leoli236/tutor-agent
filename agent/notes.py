"""
笔记整理模块

将老师语音转写或随手记下的零散文字，整理成结构清晰的教学笔记：
- Markdown 格式、分点清晰
- 自动提炼待办事项
- 自动给出下次课重点
"""

from agent.llm_client import chat_text


NOTES_SYSTEM_PROMPT = """你是一名家教助教 Agent，擅长把老师口述的零散内容整理成结构清晰的笔记。

## 整理规范
- 使用 Markdown 格式，分点清晰
- 按主题自动分组归类
- 必要时在末尾加「待办事项」和「下次课重点」
- 忠于原文信息，不编造内容；老师没说的不要推测
- 保留具体细节（数字、页码、学生表现等）

## 输出结构参考
# 📔 教学笔记

## 📌 核心要点
（分点整理）

## 📝 详细内容
（按主题分组）

## ✅ 待办事项
- [ ] ...

## 🎯 下次课重点
- ...

直接输出 Markdown，不要额外说明。"""


def organize_notes(raw_text: str) -> str:
    """
    整理零散笔记

    Args:
        raw_text: 老师口述/随手记的零散文字（可包含语音转写文本）

    Returns:
        str: 结构化 Markdown 笔记
    """
    return chat_text(
        NOTES_SYSTEM_PROMPT,
        f"## 老师的零散记录\n{raw_text}\n\n请整理成结构化教学笔记。",
        temperature=0.4,
        max_tokens=2048,
    )
