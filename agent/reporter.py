"""
学情周报生成模块

自动汇总一周内的错题、练习、辅导数据，
生成面向家长的可读报告，包含：
- 本周错题概览
- 薄弱知识点排行
- 练习正确率趋势
- 教师评语（AI 生成的建议）
"""

import json
from datetime import datetime, timedelta

from agent.llm_client import chat_text
import db


REPORT_SYSTEM_PROMPT = """你是一位负责任的教师，正在撰写给家长的学生周报。

## 报告要求
- 语气温暖专业，让家长感受到你对孩子的关注
- 先说进步，再谈需要加强的地方
- 给出具体的、可操作的家庭辅导建议
- 使用 Emoji 适当点缀（不过分）
- 控制在 300-400 字

## 格式参考
📌 **本周学习概览**
📊 **错题分析**
✅ **练习完成情况**
🎯 **下周学习建议**"""


def generate_weekly_report(student_id: int, weeks: int = 1) -> str:
    """
    生成学生周报

    Args:
        student_id: 学生ID
        weeks: 回溯几周

    Returns:
        str: 周报 Markdown 文本
    """
    student = db.get_student(student_id)
    if not student:
        return "未找到该学生信息。"

    stats = db.get_student_stats(student_id)

    # 获取具体错题
    since = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y-%m-%d %H:%M:%S")
    conn = db.get_db()
    recent_wrong = conn.execute(
        """SELECT subject, knowledge_point, error_type, question_text, created_at
           FROM wrong_questions
           WHERE student_id = ? AND created_at >= ?
           ORDER BY created_at DESC LIMIT 20""",
        (student_id, since),
    ).fetchall()
    conn.close()

    # 构建数据摘要
    wrong_summary = []
    for r in recent_wrong:
        wrong_summary.append({
            "subject": r["subject"],
            "point": r["knowledge_point"],
            "error": r["error_type"],
            "date": r["created_at"][:10],
        })

    data_desc = f"""## 学生信息
姓名：{student['name']}
年级：{student.get('grade', '未知')}

## 本周统计数据
- 错题按学科分布：{json.dumps(stats.get('wrong_by_subject', {}), ensure_ascii=False)}
- 错误类型分布：{json.dumps(stats.get('error_type_dist', {}), ensure_ascii=False)}
- 薄弱知识点排行：{json.dumps(stats.get('weak_points', []), ensure_ascii=False)}
- 变式练习完成数：{stats.get('practice_total', 0)}
- 变式练习正确率：{stats.get('practice_accuracy', 0)}%

## 近期错题明细
{json.dumps(wrong_summary, ensure_ascii=False, indent=2)}

请根据以上数据生成一份给家长的周报。"""

    report = chat_text(REPORT_SYSTEM_PROMPT, data_desc, temperature=0.7, max_tokens=1024)
    return report
