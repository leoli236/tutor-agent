"""
苏格拉底式辅导模块

核心原则：**不直接给答案**，通过逐步引导提问帮助学生自己发现错误、理解知识。
增强：辅导结束后自动输出课程记录摘要（含掌握情况、下次课计划）。
"""

from agent.llm_client import chat_text


TUTOR_SYSTEM_PROMPT = """你是一名耐心、善于引导的家教老师。
你的学生是 1 对 1 的小学生或初中生。

## 核心原则
- **绝不直接给出答案**
- 通过提问引导学生自己思考和发现
- 每次回复只问一个问题或给一个极简提示
- 对学生的每一个回复都先给予建设性反馈，再追问

## 辅导流程
1. 请学生先解释自己的思路："能跟我说说你是怎么想的吗？"
2. 找到学生思路中的关键偏差点，用提问指向该偏差
3. 如果学生卡住，给出一个方向性提示（非答案）
4. 学生接近正确方向时给予鼓励
5. 学生得出正确答案后，追问"能总结一下这道题的关键是什么吗？"
6. 最后帮助学生梳理知识点脉络

## 回复要求
- 语气亲切自然，像面对面聊天
- 用词简单，适合中小学生理解
- 每条回复 2-4 句话
- 适当使用表情符号增加亲和力
- 数学公式用 $...$ 表示"""


def generate_tutor_message(
    question_text: str,
    student_answer: str,
    correct_answer: str,
    error_type: str,
    knowledge_point: str,
    analysis: str,
    chat_history: list,
    student_latest_message: str = "",
    hint_level: int = 0,
) -> str:
    context = f"""## 当前辅导的题目
{question_text}

## 学生最初的答案
{student_answer}

## 错误类型：{error_type}
## 薄弱知识点：{knowledge_point}
## 归因分析：{analysis}

## 对话历史
"""

    if not chat_history and not student_latest_message:
        user_msg = context + "这是第一轮辅导，请主动开场引导学生。"
        return chat_text(TUTOR_SYSTEM_PROMPT, user_msg, temperature=0.7)

    for msg in chat_history[-10:]:
        role_label = "老师" if msg.get("role") == "assistant" else "学生"
        context += f"{role_label}：{msg.get('content', '')}\n"

    if student_latest_message:
        context += f"\n## 学生最新回复\n{student_latest_message}"

    if hint_level > 0:
        context += f"\n\n注意：学生已经卡住 {hint_level} 次，可以适当给出更明显的提示（但仍不要直接给答案）。"

    return chat_text(TUTOR_SYSTEM_PROMPT, context, temperature=0.7)


def summarize_session(question_text, knowledge_point, chat_history):
    """辅导结束后，生成课程记录摘要"""
    system = """你是一名家教助教。根据辅导对话，输出一份简洁的课程记录摘要。
严格返回 JSON：
{
  "mastery": "学生对该知识点的掌握情况判断（已掌握/部分掌握/未掌握）",
  "plan_next": "下次课针对该知识点的计划"
}"""
    history_text = "\n".join(
        f"{'老师' if m['role']=='assistant' else '学生'}：{m['content']}"
        for m in chat_history[-20:]
    )
    return chat_text_json(system, f"题目：{question_text}\n知识点：{knowledge_point}\n\n对话：\n{history_text}", temperature=0.3)
