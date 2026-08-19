"""
作文批改模块

接收学生作文文字（或图片识别后的文字），给出：
- 错误类型标注（语法/拼写/用词/结构）
- 逐段修改建议
- 润色后的范文
- 评分建议（百分制）
"""

from agent.llm_client import chat_text, chat_text_json


ESSAY_CORRECT_SYSTEM_PROMPT = """你是一名资深英语家教老师，擅长批改学生的英语作文。
你的批改风格严谨但鼓励性强，让学生既看到不足也获得信心。

## 批改规范
- 先指出错误类型（语法/拼写/用词/结构），再给出修改建议和总体评价
- 每个错误用 [原文] → [修改] 的格式标注
- 最后给出润色版范文和评分建议

## 输出格式（严格 JSON）
{
  "overall_score": 85,
  "errors": [
    {
      "type": "语法|拼写|用词|结构",
      "original": "原文片段",
      "correction": "修改建议",
      "explanation": "为什么这样改"
    }
  ],
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "polished_version": "润色后的完整作文",
  "comment": "总体评价和鼓励，50-100字"
}

注意：
- 只返回 JSON
- overall_score 范围 60-100
- errors 数量根据实际错误数量，不超过 10 个
- polished_version 保持原意，语言更地道
- comment 先说进步再谈不足"""


def correct_essay(essay_text: str, grade: str = "初中") -> dict:
    """
    批改英语作文

    Args:
        essay_text: 作文正文
        grade: 学生年级

    Returns:
        dict: {overall_score, errors, strengths, weaknesses, polished_version, comment}
    """
    user_msg = f"## 学生年级：{grade}\n\n## 作文内容\n{essay_text}\n\n请批改以上作文。"
    return chat_text_json(ESSAY_CORRECT_SYSTEM_PROMPT, user_msg, temperature=0.3, max_tokens=4096)


def correct_chinese_essay(essay_text: str, grade: str = "初中") -> dict:
    """
    批改中文作文（用同一个结构，换中文 prompt）
    """
    system = """你是一名资深语文家教老师，擅长批改学生的作文。
批改时先指出错误类型（病句/错别字/用词/结构），再给出修改建议和总体评价。

输出严格 JSON：
{
  "overall_score": 85,
  "errors": [
    {"type": "病句|错别字|用词|结构|逻辑", "original": "原文", "correction": "修改", "explanation": "原因"}
  ],
  "strengths": ["优点"],
  "weaknesses": ["不足"],
  "polished_version": "润色后的完整作文",
  "comment": "总体评价和鼓励"
}
只返回 JSON。"""
    user_msg = f"## 学生年级：{grade}\n\n## 作文内容\n{essay_text}"
    return chat_text_json(system, user_msg, temperature=0.3, max_tokens=4096)
