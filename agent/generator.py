"""
变式练习生成模块

根据错题的知识点，生成 3 道难度递进的变式练习题：
- 第1题：基础巩固（同知识点，直接应用）
- 第2题：稍作变化（改变条件或题型）
- 第3题：综合提升（结合其他知识点）

每道题附带参考答案和引导性提示。
增强：同时输出下次课的教学计划建议。
"""

from agent.llm_client import chat_text_json


GENERATOR_SYSTEM_PROMPT = """你是一名家教助教 Agent，专为 1 对 1 家教老师设计练习题。
你需要围绕学生的薄弱知识点生成梯度练习题，让学生逐步巩固。

## 任务
根据原始错题和归因分析，围绕薄弱知识点生成 3 道变式练习题，难度递进。

## 输出格式（严格 JSON）
{
  "problems": [
    {
      "difficulty": "基础",
      "problem_text": "题目内容",
      "answer": "参考答案及解题过程",
      "hint": "引导性提问（不给答案）"
    },
    {
      "difficulty": "中等",
      "problem_text": "...",
      "answer": "...",
      "hint": "..."
    },
    {
      "difficulty": "提升",
      "problem_text": "...",
      "answer": "...",
      "hint": "..."
    }
  ],
  "homework_suggestion": "布置给学生的课后作业建议，50字以内"
}

出题要求：
1. 变式题必须考查相同的知识点，但情境/数据/题型要与原题不同
2. 难度梯度清晰：基础→中等→提升
3. 数学公式用 $...$，Python 题保持代码格式
4. 题目表述适合对应年级
5. hint 是引导性提问，不透露答案
6. 只返回 JSON"""


def generate_variations(question_text: str, knowledge_point: str,
                       subject: str, student_answer: str,
                       correct_answer: str, difficulty: str = "中等") -> dict:
    result_text = chat_text_json(
        GENERATOR_SYSTEM_PROMPT,
        f"""## 学科：{subject}
## 原始错题：{question_text}
## 学生的错误答案：{student_answer}
## 正确答案：{correct_answer}
## 薄弱知识点：{knowledge_point}
## 原题难度：{difficulty}

请围绕薄弱知识点生成 3 道变式练习题。""",
        temperature=0.6,
    )
    return result_text
