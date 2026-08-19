"""
错题识别模块（OCR）

从学生上传的错题照片中提取：
- 题目原文
- 学生的作答
- 初步判断的学科
"""

from agent.llm_client import chat_vision_json


OCR_SYSTEM_PROMPT = """你是一位经验丰富的教师助手，擅长从学生作业照片中识别题目内容。

你的任务：仔细观察图片，提取以下信息并以 JSON 返回。

输出格式：
{
  "question_text": "题目完整文字，含数学公式（用LaTeX）或代码",
  "student_answer": "学生在图片上写的答案，如无法辨认则写'无法识别'",
  "subject_guess": "数学|英语|Python编程",
  "is_handwritten": true/false,
  "image_quality": "清晰|模糊|倾斜|部分遮挡"
}

注意：
- 数学公式用 $...$ 包裹（行内）或 $$...$$ 包裹（独立行）
- Python 代码保留原始缩进
- 如果图片中只有题目没有学生答案，student_answer 填空字符串
- 只返回 JSON，不要额外说明"""


def recognize_question(image_path: str, hint_text: str = "") -> dict:
    """
    识别错题图片

    Args:
        image_path: 错题照片路径
        hint_text: 教师提供的额外提示（可选）

    Returns:
        dict: {question_text, student_answer, subject_guess, is_handwritten, image_quality}
    """
    user_text = ""
    if hint_text:
        user_text = f"教师备注：{hint_text}\n\n"

    result = chat_vision_json(OCR_SYSTEM_PROMPT, image_path, user_text)
    return result
