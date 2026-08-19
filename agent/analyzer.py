"""
错题归因分析模块

对识别出的错题进行深度分析：
- 判断错误类型（知识性错误 / 审题不清 / 计算粗心 / 逻辑混乱等）
- 定位薄弱知识点
- 给出讲解思路（不直接给答案）
- 给出参考正确答案
- 输出格式对齐上传文件中的 📅👤📘📝📋✅💰 规范
"""

from agent.llm_client import chat_text_json

from config import ERROR_TYPES


ANALYZER_SYSTEM_PROMPT = f"""你是一名家教助教 Agent，专为 1 对 1 家教老师服务。
你负责精准诊断学生的错题原因，帮老师了解学生真实掌握情况，以便下次课重点讲解。

## 错误类型（必须从中选一个最贴切的）
{', '.join(ERROR_TYPES)}

## 你的任务
仔细分析以下题目和学生答案，判断错误原因并定位薄弱知识点。
记录时使用规范格式，方便老师查阅。

## 输出格式（严格 JSON）
{{
  "error_type": "上面列出的错误类型之一",
  "knowledge_point": "1-3个关键词，用顿号分隔",
  "analysis": "面向教师的详细分析，说明学生错在哪里、为什么错，100-200字",
  "correct_answer": "题目的正确解答过程，步骤清晰",
  "difficulty": "基础|中等|较难",
  "teaching_strategy": "给教师的教学建议，如何讲解这个知识点最有效，50-100字",
  "next_plan": "下次课针对这个知识点的教学计划建议"
}}

注意：
- 只返回 JSON
- 教学建议要具体，包含可操作的讲解步骤
- 如果涉及多个知识点缺失，全部列出"""


def analyze_error(question_text: str, student_answer: str,
                   subject: str, correct_answer_hint: str = "") -> dict:
    """
    分析错题原因

    Args:
        question_text: 题目原文
        student_answer: 学生的作答
        subject: 学科（数学/英语/Python编程）
        correct_answer_hint: 教师提供的正确答案参考（可选）

    Returns:
        dict: {error_type, knowledge_point, analysis, correct_answer,
               difficulty, teaching_strategy, next_plan}
    """
    user_msg = f"""## 学科
{subject}

## 题目
{question_text}

## 学生的答案
{student_answer}
"""
    if correct_answer_hint:
        user_msg += f"\n## 教师提供的参考答案\n{correct_answer_hint}\n"

    result = chat_text_json(ANALYZER_SYSTEM_PROMPT, user_msg, temperature=0.2)
    return result
