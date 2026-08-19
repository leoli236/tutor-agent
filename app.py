"""
AI 家教工作台 —— 完整版

基于《家教Agent系统提示词.md》实现 7 大核心能力：
1. 学生档案管理（含课时费）
2. 课程记录（📅👤📘📝📋✅💰 规范格式）
3. 资料库管理（学科 × 年级分类）
4. 作文批改（英语/语文）
5. 错题归因 + 变式练习 + 苏格拉底辅导
6. 收入记录（按学生/月份统计）
7. 课表生成（周视图）
"""

import sys
import os
import uuid
import json

import streamlit as st
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db
from agent.ocr import recognize_question
from agent.analyzer import analyze_error
from agent.generator import generate_variations
from agent.tutor import generate_tutor_message
from agent.reporter import generate_weekly_report
from agent.essay import correct_essay, correct_chinese_essay
from agent.notes import organize_notes
from agent.llm_client import chat_text_json

from config import SUBJECTS, GRADES, UPLOAD_DIR


# ══════════════════════════════════════════════════════════════
#  全局样式
# ══════════════════════════════════════════════════════════════

def inject_css():
    st.markdown("""
<style>
.stApp { background-color: #FFFDF7 !important; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.stApp > header {
    background: linear-gradient(135deg, #F4A261 0%, #E76F51 50%, #264653 100%) !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFF8F0 0%, #FFECD2 100%) !important;
    width: 300px !important;
    min-width: 300px !important;
    max-width: 300px !important;
}

/* ── 品牌区 ── */
.sb-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 4px 10px;
}
.sb-brand-icon {
    font-size: 2.4rem;
    background: linear-gradient(135deg, #F4A261, #E76F51);
    width: 56px;
    height: 56px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(244, 162, 97, 0.35);
    flex-shrink: 0;
}
.sb-brand-title {
    font-size: 1.25rem;
    font-weight: 800;
    color: #264653;
    line-height: 1.3;
}
.sb-brand-sub {
    font-size: 0.82rem;
    color: #8B7355;
    margin-top: 2px;
}

/* ── 导航菜单（Radio 美化为菜单卡片） ── */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 6px;
    width: 100%;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: #FFFFFF;
    border: 1px solid #F0E6D8;
    border-radius: 14px;
    padding: 12px 14px !important;
    margin: 0 0 2px 0;
    transition: all 0.2s ease;
    cursor: pointer;
    width: 100%;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    border-color: #F4A261;
    background: #FFF8F0;
    transform: translateX(4px);
    box-shadow: 0 3px 10px rgba(244, 162, 97, 0.15);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #264653 !important;
    line-height: 1.4 !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, #F4A261, #E76F51) !important;
    border-color: transparent !important;
    box-shadow: 0 4px 14px rgba(231, 111, 81, 0.4) !important;
    transform: translateX(4px);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
    color: #FFFFFF !important;
}
/* 隐藏单选圆圈，纯菜单观感 */
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-of-type {
    display: none !important;
}

/* ── 侧边栏通用字体放大 ── */
section[data-testid="stSidebar"] {
    font-size: 1rem;
}
section[data-testid="stSidebar"] .stSelectbox label p,
section[data-testid="stSidebar"] .stTextInput label p,
section[data-testid="stSidebar"] .stNumberInput label p,
section[data-testid="stSidebar"] .stMultiselect label p {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #5C4A3A;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    font-size: 1rem !important;
    min-height: 44px;
    display: flex;
    align-items: center;
}
section[data-testid="stSidebar"] details summary p {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #264653;
}
section[data-testid="stSidebar"] details summary:hover {
    color: #E76F51;
}

/* ── 分区标题 ── */
.sb-section-label {
    font-size: 0.85rem;
    font-weight: 700;
    color: #B08968;
    letter-spacing: 1px;
    margin: 14px 0 8px;
    padding-left: 4px;
}

/* ── 学生信息卡 ── */
.sb-student-card {
    background: #FFFFFF;
    border: 1px solid #F0E6D8;
    border-radius: 16px;
    padding: 14px 16px;
    margin-top: 8px;
    box-shadow: 0 3px 12px rgba(244, 162, 97, 0.10);
}
.sb-student-name {
    font-size: 1.15rem;
    font-weight: 800;
    color: #264653;
}
.sb-student-meta {
    font-size: 0.82rem;
    color: #8B7355;
    margin: 4px 0 10px;
    line-height: 1.5;
}
.sb-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.sb-chip {
    font-size: 0.8rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 10px;
}
.chip-orange { background: #FFF0E0; color: #E76F51; }
.chip-green  { background: #E8F5E9; color: #2D6A4F; }
.chip-blue   { background: #E3F2FD; color: #457B9D; }

/* 主按钮 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #F4A261, #E76F51) !important;
    color: white !important;
    border: none !important;
    border-radius: 25px !important;
    padding: 10px 28px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(244, 162, 97, 0.35) !important;
    transition: all 0.3s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(244, 162, 97, 0.5) !important;
}
.stButton > button:not([kind="primary"]) {
    background: transparent !important;
    color: #457B9D !important;
    border: 2px solid #457B9D !important;
    border-radius: 25px !important;
    padding: 8px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: #457B9D !important;
    color: white !important;
    transform: translateY(-2px) !important;
}

/* 卡片 */
.warm-card {
    background: #FFFFFF;
    border: 1px solid #F0E6D8;
    border-radius: 16px;
    padding: 24px;
    margin: 8px 0;
    box-shadow: 0 4px 15px rgba(244, 162, 97, 0.10);
    transition: all 0.3s ease;
}
.warm-card:hover {
    box-shadow: 0 8px 25px rgba(244, 162, 97, 0.18);
}

.metric-card {
    background: #FFFFFF;
    border: 1px solid #F0E6D8;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(244, 162, 97, 0.10);
    border-left: 4px solid #F4A261;
    transition: all 0.3s ease;
}
.metric-card:hover { transform: translateY(-3px); }

.icon-card {
    background: white;
    border-radius: 20px;
    padding: 24px 16px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    transition: all 0.3s ease;
    border: 2px solid transparent;
}
.icon-card:hover {
    border-color: #F4A261;
    transform: scale(1.03);
    box-shadow: 0 8px 25px rgba(244, 162, 97, 0.2);
}
.icon-card .emoji { font-size: 2.8rem; display: block; margin-bottom: 8px; }
.icon-card .label { font-weight: 700; color: #264653; font-size: 0.95rem; }

/* 提示框 */
.stSuccess { background-color: #E8F5E9 !important; border: 1px solid #81B29A !important; border-radius: 12px !important; }
.stWarning { background-color: #FFF8E1 !important; border: 1px solid #F4A261 !important; border-radius: 12px !important; }
.stError { background-color: #FFEBEE !important; border: 1px solid #E07A5F !important; border-radius: 12px !important; }
.stInfo { background-color: #E3F2FD !important; border: 1px solid #457B9D !important; border-radius: 12px !important; }

/* 输入框 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 12px !important;
    border: 2px solid #F0E6D8 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #F4A261 !important;
    box-shadow: 0 0 0 3px rgba(244, 162, 97, 0.15) !important;
}

/* 上传 */
[data-testid="stFileUploader"] {
    border: 2px dashed #F4A261 !important;
    border-radius: 16px !important;
    background: #FFF8F0 !important;
    padding: 16px !important;
}

/* 聊天气泡 */
.tutor-bubble {
    background: #FFF0E0;
    border: 1px solid #F0E6D8;
    border-radius: 18px 18px 18px 4px;
    padding: 14px 20px;
    margin: 8px 0;
    color: #264653;
    line-height: 1.7;
}
.student-bubble {
    background: linear-gradient(135deg, #457B9D, #2A9D8F);
    border-radius: 18px 18px 4px 18px;
    padding: 14px 20px;
    margin: 8px 0 8px 40px;
    color: white;
    line-height: 1.7;
}

hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, #F4A261, transparent);
}

.section-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #264653;
    padding-bottom: 10px;
    border-bottom: 3px solid #F4A261;
    margin-bottom: 20px;
    display: inline-block;
}

/* 课表 */
.schedule-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 4px;
}
.schedule-table th {
    background: linear-gradient(135deg, #F4A261, #E76F51);
    color: white;
    padding: 10px 8px;
    border-radius: 10px;
    font-size: 0.9rem;
}
.schedule-table td {
    background: #FFFFFF;
    border: 1px solid #F0E6D8;
    padding: 8px;
    border-radius: 10px;
    vertical-align: top;
    min-height: 60px;
    font-size: 0.85rem;
}
.schedule-lesson {
    background: #FFF0E0;
    border-left: 3px solid #E76F51;
    padding: 4px 8px;
    border-radius: 6px;
    margin: 3px 0;
    font-size: 0.8rem;
    color: #264653;
}

/* 下载按钮 */
.stDownloadButton > button {
    background: linear-gradient(135deg, #2A9D8F, #457B9D) !important;
    color: white !important;
    border: none !important;
    border-radius: 25px !important;
    font-weight: 600 !important;
}

/* Product UI refinement: calmer workbench surfaces and clearer hierarchy. */
.stApp { background: #F7F8FA !important; color: #25313C; }
.stApp > header { background: #F7F8FA !important; }
#MainMenu, footer { display: none !important; }
/* Keep Streamlit's toolbar visible: it contains the sidebar toggle on collapsed layouts. */

section[data-testid="stSidebar"] {
    background: #F1F3F5 !important;
    border-right: 1px solid #DCE1E6;
    width: 272px !important;
    min-width: 272px !important;
    max-width: 272px !important;
}
section[data-testid="stSidebar"] > div:first-child { padding: 22px 16px 24px; }
.sb-brand { padding: 4px 6px 22px; gap: 10px; }
.sb-brand-icon {
    width: 42px; height: 42px; border-radius: 10px;
    background: #E76F51; box-shadow: none; font-size: 1.75rem;
}
.sb-brand-title { color: #24313B; font-size: 1.08rem; letter-spacing: 0; }
.sb-brand-sub { color: #7A8792; font-size: .76rem; }
.sb-section-label { color: #8A96A1; font-size: .72rem; letter-spacing: 1.4px; margin: 14px 6px 8px; }
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 3px; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: transparent; border: 1px solid transparent; border-radius: 8px;
    padding: 9px 10px !important; margin: 0; box-shadow: none; transform: none;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: #E5E9ED; border-color: transparent; transform: none; box-shadow: none;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    color: #52606B !important; font-size: .92rem !important; font-weight: 600 !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: #FFFFFF !important; border-color: #D8DEE4 !important;
    box-shadow: 0 2px 8px rgba(36,49,59,.06) !important; transform: none;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p { color: #D95D43 !important; }
.sb-student-card { background: #FFFFFF; border: 1px solid #DCE1E6; border-radius: 8px; box-shadow: none; padding: 12px; }
.sb-student-name { color: #24313B; font-size: 1rem; }
.sb-student-meta { color: #7A8792; }
.sb-chip { border-radius: 6px; font-size: .72rem; padding: 3px 7px; }

section.main > div { max-width: 1180px; padding-top: 28px; }
.section-title {
    color: #24313B; font-size: 1.12rem; letter-spacing: 0; border-bottom: 2px solid #E76F51;
    margin: 0 0 18px; padding-bottom: 8px;
}
hr { height: 1px; background: #DCE1E6; margin: 24px 0; }
.metric-card, .warm-card, .icon-card {
    background: #FFFFFF; border: 1px solid #DCE1E6; border-radius: 8px;
    box-shadow: 0 2px 8px rgba(36,49,59,.04); transition: border-color .2s ease, box-shadow .2s ease;
}
.metric-card { padding: 16px; border-left-width: 3px; text-align: left; }
.metric-card:hover, .warm-card:hover, .icon-card:hover { transform: none; box-shadow: 0 4px 14px rgba(36,49,59,.08); border-color: #C8D0D7; }
.metric-card > div:first-child { font-size: 1.35rem !important; }
.metric-card > div:nth-child(2) { font-size: 1.55rem !important; color: #24313B !important; }
.icon-card { border-width: 1px; border-radius: 8px; padding: 18px 16px; text-align: left; }
.icon-card .emoji { font-size: 1.75rem; margin-bottom: 10px; }
.icon-card .label { color: #24313B; font-size: .98rem; }
.student-overview-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 14px; }
.student-overview-grid div { background: #F7F8FA; border: 1px solid #E7EBEF; border-radius: 6px; padding: 8px; }
.student-overview-grid span { display: block; color: #7A8792; font-size: .7rem; }
.student-overview-grid strong { display: block; color: #24313B; font-size: 1rem; margin-top: 3px; }
.student-card-footer { color: #7A8792; font-size: .78rem; margin-top: 12px; }
.icon-card > div:last-child { display: none !important; }
.stButton > button, .stDownloadButton > button {
    border-radius: 7px !important; min-height: 40px; font-size: .9rem !important;
    box-shadow: none !important; transform: none !important;
}
.stButton > button[kind="primary"] { background: #D95D43 !important; }
.stButton > button[kind="primary"]:hover { background: #C84F37 !important; }
.stButton > button:not([kind="primary"]) { color: #52606B !important; border: 1px solid #CBD3DA !important; background: #FFFFFF !important; }
.stButton > button:not([kind="primary"]):hover { color: #24313B !important; background: #F1F3F5 !important; }
.stDownloadButton > button { background: #2A9D8F !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    border-radius: 7px !important; border: 1px solid #CBD3DA !important; background: #FFFFFF !important;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #E76F51 !important; box-shadow: 0 0 0 2px rgba(231,111,81,.12) !important; }
[data-testid="stFileUploader"] { border: 1px dashed #B9C3CC !important; border-radius: 8px !important; background: #FFFFFF !important; padding: 12px !important; }
details[data-testid="stExpander"] { border: 1px solid #DCE1E6; border-radius: 8px; background: #FFFFFF; }
.tutor-bubble, .student-bubble { border-radius: 8px; box-shadow: none; }

@media (max-width: 900px) {
    section[data-testid="stSidebar"] { width: 240px !important; min-width: 240px !important; }
    section.main > div { padding: 20px 16px; }
    .metric-card { padding: 12px; }
}
</style>
""", unsafe_allow_html=True)


def ensure_uploads_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def render_metric_card(container, emoji, label, value, color="#F4A261"):
    container.markdown(f"""
    <div class="metric-card" style="border-left-color: {color};">
        <div style="font-size: 2rem; margin-bottom: 4px;">{emoji}</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #264653;">{value}</div>
        <div style="font-size: 0.85rem; color: #6B7280; margin-top: 2px;">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  页面配置
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AI 家教工作台",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

if "current_student" not in st.session_state:
    st.session_state.current_student = None


# ══════════════════════════════════════════════════════════════
#  侧边栏：导航 + 学生管理
# ══════════════════════════════════════════════════════════════

PAGES = [
    "🏠 首页总览",
    "📝 错题录入",
    "✏️ 变式练习",
    "🗣️ 苏格拉底辅导",
    "✍️ 作文批改",
    "📔 笔记整理",
    "📖 课程日志",
    "📅 周课表",
    "💰 收入统计",
    "📁 资料库",
    "📊 学情周报",
]


def render_sidebar():
    st.sidebar.markdown("""
    <div class="sb-brand">
        <div class="sb-brand-icon">🏠</div>
        <div>
            <div class="sb-brand-title">AI 家教工作台</div>
            <div class="sb-brand-sub">让教学更高效 · 让学习更温暖</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sb-section-label">功 能 导 航</div>', unsafe_allow_html=True)

    # 导航
    page = st.sidebar.radio("导航", PAGES, key="page_nav", label_visibility="collapsed")

    st.sidebar.markdown('<div class="sb-section-label">学 生 管 理</div>', unsafe_allow_html=True)

    # 学生管理
    with st.sidebar.expander("➕ 添加新学生", expanded=False):
        name = st.text_input("姓名", key="new_name", placeholder="输入学生姓名")
        grade = st.selectbox("年级", GRADES, key="new_grade")
        subjects = st.multiselect("辅导学科", SUBJECTS, key="new_subjects")
        rate = st.number_input("课时费（元/课时）", min_value=0, value=100, step=50, key="new_rate")
        if st.button("✨ 添加学生", key="add_btn", use_container_width=True):
            if name.strip():
                sid = db.add_student(name.strip(), grade, subjects, hourly_rate=rate)
                st.session_state.current_student = sid
                st.success(f"🎉 已添加：{name}")
                st.rerun()

    students = db.list_students()
    if students:
        options = ["-- 请选择 --"] + [f"{s['name']}（{s.get('grade', '')}）" for s in students]
        idx = 0
        for i, s in enumerate(students):
            if s["id"] == st.session_state.current_student:
                idx = i + 1
                break
        selected = st.sidebar.selectbox("", options, index=idx, key="stu_sel",
                                         label_visibility="collapsed")
        if selected != "-- 请选择 --":
            st.session_state.current_student = students[options.index(selected) - 1]["id"]
        else:
            st.session_state.current_student = None

        if st.session_state.current_student:
            student = db.get_student(st.session_state.current_student)
            stats = db.get_student_stats(st.session_state.current_student)
            subjects = json.loads(student.get("subjects") or "[]")
            meta_parts = [p for p in [student.get("grade", ""),
                                      "、".join(subjects)] if p]
            meta_parts.append(f"¥{student.get('hourly_rate', 0) or 0}/课时")
            st.sidebar.markdown(f"""
            <div class="sb-student-card">
                <div class="sb-student-name">🎓 {student['name']}</div>
                <div class="sb-student-meta">{' · '.join(meta_parts)}</div>
                <div class="sb-chips">
                    <span class="sb-chip chip-orange">📝 错题 {sum(stats.get('wrong_by_subject', {}).values())}</span>
                    <span class="sb-chip chip-green">✅ 正确率 {stats.get('practice_accuracy', 0)}%</span>
                    <span class="sb-chip chip-blue">📚 已上 {stats.get('total_lessons', 0)} 课</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.sidebar.info("👈 先添加一位学生吧！")

    return page


# ══════════════════════════════════════════════════════════════
#  🏠 首页总览
# ══════════════════════════════════════════════════════════════

def render_dashboard():
    students = db.list_students()
    if not students:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px;">
            <div style="font-size: 4rem; margin-bottom: 16px;">🌟</div>
            <h2 style="color: #264653;">欢迎来到 AI 家教工作台</h2>
            <p style="color: #6B7280; font-size: 1.1rem;">在左侧添加你的第一位学生，开始智能教学之旅 ✈️</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown('<div class="section-title">📊 教学总览</div>', unsafe_allow_html=True)

    from datetime import datetime
    this_month = datetime.now().strftime("%Y-%m")

    total_wrong = sum(sum(db.get_student_stats(s["id"]).get("wrong_by_subject", {}).values()) for s in students)
    month_income = db.get_monthly_income(month=this_month)

    c1, c2, c3, c4 = st.columns(4)
    render_metric_card(c1, "👨‍🎓", "学生数", len(students))
    render_metric_card(c2, "📝", "错题总数", total_wrong, color="#E07A5F")
    render_metric_card(c3, "📅", "本月课程", month_income["lesson_count"], color="#457B9D")
    render_metric_card(c4, "💰", "本月收入", f"¥{month_income['total']:,.0f}", color="#81B29A")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">👨‍🎓 我的学生</div>', unsafe_allow_html=True)

    cols = st.columns(min(len(students), 4))
    for i, student in enumerate(students):
        stats = db.get_student_stats(student["id"])
        subjects = json.loads(student.get("subjects") or "[]")
        emoji = {"数学": "📐", "英语": "📖", "Python编程": "💻"}.get(subjects[0] if subjects else "", "📚")
        wrong_count = sum(stats.get("wrong_by_subject", {}).values())
        with cols[i % len(cols)]:
            st.markdown(f"""
            <div class="icon-card">
                <span class="emoji">{emoji}</span>
                <span class="label">{student['name']}</span>
                <div style="font-size:0.8rem;color:#6B7280;">{student.get('grade', '')}</div>
                <div class="student-overview-grid">
                    <div><span>课程</span><strong>{stats.get('total_lessons', 0)}</strong></div>
                    <div><span>错题</span><strong>{wrong_count}</strong></div>
                    <div><span>练习正确率</span><strong>{stats.get('practice_accuracy', 0)}%</strong></div>
                </div>
                <div class="student-card-footer">累计收入 ¥{stats.get('total_income', 0):,.0f}</div>
                <div style="margin-top:8px;">
                    <span style="display:inline-block;background:#FFF0E0;color:#E76F51;padding:2px 10px;border-radius:10px;font-size:0.75rem;font-weight:600;">
                        已上 {stats.get('total_lessons', 0)} 课
                    </span>
                    <span style="display:inline-block;background:#E8F5E9;color:#2D6A4F;padding:2px 10px;border-radius:10px;font-size:0.75rem;font-weight:600;margin-left:4px;">
                        累计 ¥{stats.get('total_income', 0):,.0f}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  📝 错题录入
# ══════════════════════════════════════════════════════════════

def render_wrong_question_input():
    if not st.session_state.current_student:
        st.info("👈 请先在左侧选择一位学生")
        return

    student = db.get_student(st.session_state.current_student)
    st.markdown('<div class="section-title">📝 错题录入</div>', unsafe_allow_html=True)
    st.markdown(f"当前学生：**{student['name']}**（{student.get('grade', '')}）")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### 📸 上传错题照片")
        uploaded = st.file_uploader("", type=["jpg", "jpeg", "png", "webp"],
                                     key="wq_upload", label_visibility="collapsed")
        if uploaded:
            st.image(Image.open(uploaded), use_column_width=True)
    with col_right:
        st.markdown("### ℹ️ 补充信息")
        subject = st.selectbox("学科", SUBJECTS, key="wq_subj")
        hint = st.text_area("教师备注（可选）", key="wq_hint")
        correct_hint = st.text_area("参考答案（可选）", key="wq_correct")

    if uploaded and st.button("🔍 识别题目 → 归因 → 出题（一键全流程）", type="primary", use_container_width=True):
        ensure_uploads_dir()
        ext = os.path.splitext(uploaded.name)[1]
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
        with open(img_path, "wb") as f:
            f.write(uploaded.getbuffer())

        # Step 1: OCR
        with st.spinner("🔍 第1步/3：AI 识别题目..."):
            try:
                ocr_result = recognize_question(img_path, hint)
            except Exception as e:
                st.error(f"识别失败：{e}")
                return

        # Step 2: 归因
        with st.spinner("🧠 第2步/3：AI 归因分析..."):
            try:
                analysis = analyze_error(
                    ocr_result.get("question_text", ""),
                    ocr_result.get("student_answer", ""),
                    subject, correct_hint,
                )
            except Exception as e:
                st.error(f"分析失败：{e}")
                return

        # Step 3: 出题
        with st.spinner("📝 第3步/3：AI 生成变式题..."):
            try:
                variations = generate_variations(
                    ocr_result.get("question_text", ""),
                    analysis.get("knowledge_point", ""),
                    subject,
                    ocr_result.get("student_answer", ""),
                    analysis.get("correct_answer", ""),
                    analysis.get("difficulty", "中等"),
                )
            except Exception as e:
                st.error(f"出题失败：{e}")
                return

        # 保存
        problems = variations.get("problems", [])
        qid = db.add_wrong_question(
            student_id=st.session_state.current_student,
            subject=subject,
            question_text=ocr_result.get("question_text", ""),
            student_answer=ocr_result.get("student_answer", ""),
            correct_answer=analysis.get("correct_answer", ""),
            error_type=analysis.get("error_type", ""),
            knowledge_point=analysis.get("knowledge_point", ""),
            analysis=analysis.get("analysis", ""),
            image_path=img_path,
            difficulty=analysis.get("difficulty", "中等"),
        )
        if problems:
            db.add_practice_problems(qid, problems)

        st.balloons()
        st.success(f"🎉 全流程完成！错题（ID:{qid}）已保存，生成 {len(problems)} 道变式题")

        # 展示结果
        _show_analysis_result(analysis)
        _show_variations(problems)

    # 手动录入
    st.markdown("<hr>", unsafe_allow_html=True)
    with st.expander("⌨️ 没有照片？手动录入错题"):
        m_subj = st.selectbox("学科", SUBJECTS, key="m_subj")
        m_q = st.text_area("题目内容", key="m_q", height=80)
        m_a = st.text_area("学生答案", key="m_a", height=60)
        if st.button("💾 保存手动录入", key="m_save"):
            if m_q.strip():
                qid = db.add_wrong_question(
                    st.session_state.current_student, m_subj, m_q.strip(),
                    student_answer=m_a.strip(),
                )
                st.success(f"已保存（ID:{qid}）— 可到「变式练习」页生成变式题")
                st.rerun()


def _show_analysis_result(analysis):
    a = analysis
    st.markdown("---")
    st.markdown("### 🧠 归因分析结果")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="warm-card">
            <div style="font-weight:700;color:#E07A5F;font-size:1.1rem;">{a.get('error_type', '')}</div>
            <div style="color:#6B7280;font-size:0.9rem;margin-top:4px;">薄弱点：{a.get('knowledge_point', '')}</div>
            <div style="color:#6B7280;font-size:0.9rem;">难度：{a.get('difficulty', '')}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="warm-card">
            <div style="font-size:0.85rem;color:#6B7280;">💡 教学建议</div>
            <div style="line-height:1.7;margin-top:6px;">{a.get('teaching_strategy', '')}</div>
        </div>
        """, unsafe_allow_html=True)
    with st.expander("📖 详细分析 + 参考答案"):
        st.write(a.get("analysis", ""))
        st.code(a.get("correct_answer", ""), language=None)


def _show_variations(problems):
    if not problems:
        return
    st.markdown("### 📝 变式练习题")
    diff_emoji = {"基础": "🌱", "中等": "🌿", "提升": "🌳"}
    diff_color = {"基础": "#81B29A", "中等": "#F4A261", "提升": "#E07A5F"}
    for i, p in enumerate(problems):
        st.markdown(f"""
        <div class="warm-card" style="border-left: 4px solid {diff_color.get(p.get('difficulty'), '#F4A261')};">
            <span style="margin-right:6px;">{diff_emoji.get(p.get('difficulty'), '📝')}</span>
            <strong>变式题 {i+1} · {p.get('difficulty', '')}</strong>
            <div style="line-height:1.8;margin-top:8px;">{p.get('problem_text', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("💡 提示"):
                st.info(p.get("hint", ""))
        with c2:
            with st.expander("✅ 答案"):
                st.code(p.get("answer", ""), language=None)


# ══════════════════════════════════════════════════════════════
#  ✏️ 变式练习
# ══════════════════════════════════════════════════════════════

def render_practice():
    if not st.session_state.current_student:
        st.info("👈 请先在左侧选择一位学生")
        return
    student = db.get_student(st.session_state.current_student)
    st.markdown('<div class="section-title">✏️ 变式练习</div>', unsafe_allow_html=True)
    st.markdown(f"当前学生：**{student['name']}**")

    wrong_qs = db.list_wrong_questions(student_id=st.session_state.current_student)
    if not wrong_qs:
        st.info("📚 暂无错题记录，请先在「错题录入」页添加")
        return

    subj_emoji = {"数学": "📐", "英语": "📖", "Python编程": "💻"}
    for wq in wrong_qs:
        with st.expander(f"{subj_emoji.get(wq['subject'], '📝')} {wq['question_text'][:55]}...（{wq['error_type']}）"):
            st.markdown(f"""
            <div class="warm-card">
                <span style="background:#FFF0E0;color:#E76F51;padding:3px 12px;border-radius:10px;font-size:0.8rem;font-weight:600;">{wq['subject']}</span>
                <span style="background:#FFEBEE;color:#E07A5F;padding:3px 12px;border-radius:10px;font-size:0.8rem;font-weight:600;margin-left:4px;">{wq['error_type']}</span>
                <span style="background:#E3F2FD;color:#457B9D;padding:3px 12px;border-radius:10px;font-size:0.8rem;font-weight:600;margin-left:4px;">{wq['knowledge_point']}</span>
                <div style="line-height:1.8;margin-top:10px;">{wq['question_text']}</div>
            </div>
            """, unsafe_allow_html=True)

            problems = db.get_practice_problems(wq["id"])
            if not problems:
                if st.button("📝 生成变式题", key=f"gen_{wq['id']}", use_container_width=True):
                    with st.spinner("🤖 生成中..."):
                        try:
                            v = generate_variations(
                                wq["question_text"], wq["knowledge_point"],
                                wq["subject"], wq["student_answer"],
                                wq["correct_answer"], wq.get("difficulty", "中等"),
                            )
                            db.add_practice_problems(wq["id"], v.get("problems", []))
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"生成失败：{e}")
                continue

            diff_emoji = {"基础": "🌱", "中等": "🌿", "提升": "🌳"}
            for i, p in enumerate(problems):
                st.markdown(f"""
                <div class="warm-card" style="border-left:4px solid #F4A261;">
                    <span>{diff_emoji.get(p.get('difficulty'), '📝')}</span>
                    <strong>变式题 {i+1}</strong>
                    <span style="float:right;color:#E76F51;font-size:0.85rem;font-weight:600;">{p.get('difficulty', '')}</span>
                    <div style="line-height:1.8;margin-top:8px;">{p['problem_text']}</div>
                </div>
                """, unsafe_allow_html=True)

                ans = st.text_area("你的答案 ✍️", key=f"ans_{p['id']}", height=80,
                                   placeholder="在这里写下你的答案...")
                c1, c2 = st.columns(2)
                if c1.button("✅ 提交答案", key=f"check_{p['id']}", type="primary", use_container_width=True):
                    if ans.strip():
                        with st.spinner("🤖 AI 批改中..."):
                            try:
                                judge = chat_text_json(
                                    "你是一个评判助手",
                                    f"判断学生的答案是否正确。\n题目：{p['problem_text']}\n标准答案：{p.get('answer', '')}\n学生答案：{ans}\n严格返回 JSON：{{\"is_correct\": true/false, \"feedback\": \"简短评语\"}}",
                                    temperature=0.1,
                                )
                                ok = judge.get("is_correct", False)
                                db.save_practice_session(p["id"], st.session_state.current_student, ans, ok, 0)
                                if ok:
                                    st.balloons()
                                    st.success(f"🎉 回答正确！{judge.get('feedback', '')}")
                                else:
                                    st.error(f"💪 还需努力。{judge.get('feedback', '')}")
                                    with st.expander("📖 查看正确答案"):
                                        st.code(p.get("answer", ""))
                            except Exception as e:
                                st.error(f"批改失败：{e}")
                    else:
                        st.warning("✍️ 请先填写答案再提交哦～")
                if c2.button("💡 给我提示", key=f"hint_{p['id']}", use_container_width=True):
                    st.info(f"💡 {p.get('hint', '再想想看～')}")
                st.markdown("---")


# ══════════════════════════════════════════════════════════════
#  🗣️ 苏格拉底辅导
# ══════════════════════════════════════════════════════════════

def render_tutor():
    if not st.session_state.current_student:
        st.info("👈 请先在左侧选择一位学生")
        return
    student = db.get_student(st.session_state.current_student)
    st.markdown('<div class="section-title">🗣️ 苏格拉底辅导</div>', unsafe_allow_html=True)
    st.markdown(f"当前学生：**{student['name']}** · AI 老师 🧑‍🏫 只引导不代做哦～")

    wrong_qs = db.list_wrong_questions(student_id=st.session_state.current_student)
    if not wrong_qs:
        st.info("📚 暂无错题记录")
        return

    subj_emoji = {"数学": "📐", "英语": "📖", "Python编程": "💻"}
    options = {f"{subj_emoji.get(wq['subject'], '📝')} {wq['question_text'][:40]}...": wq for wq in wrong_qs}
    selected_wq = options[st.selectbox("选择要辅导的错题", list(options.keys()))]

    st.markdown(f"""
    <div class="warm-card" style="border-left:4px solid #457B9D;">
        <div style="font-weight:700;margin-bottom:8px;">📝 题目</div>
        <div style="line-height:1.8;">{selected_wq['question_text']}</div>
        <div style="margin-top:10px;">
            <span style="background:#FFF0E0;color:#E76F51;padding:3px 10px;border-radius:8px;font-size:0.8rem;">{selected_wq['error_type']}</span>
            <span style="background:#E3F2FD;color:#457B9D;padding:3px 10px;border-radius:8px;font-size:0.8rem;margin-left:4px;">{selected_wq['knowledge_point']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    history_key = f"tutor_history_{selected_wq['id']}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    with st.container():
        for msg in st.session_state[history_key]:
            if msg["role"] == "assistant":
                st.markdown(f"""
                <div style="display:flex;align-items:flex-start;gap:8px;margin:6px 0;">
                    <span style="font-size:1.8rem;flex-shrink:0;">🧑‍🏫</span>
                    <div class="tutor-bubble">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display:flex;align-items:flex-start;gap:8px;margin:6px 0;flex-direction:row-reverse;">
                    <span style="font-size:1.8rem;flex-shrink:0;">👦</span>
                    <div class="student-bubble">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    student_msg = st.text_area("💬 学生的回复", key="tutor_input", height=80,
                                placeholder="在这里输入学生的回复...")

    c_send, c_stuck, c_clear = st.columns([2, 1, 1])
    if c_send.button("💬 发送", type="primary", use_container_width=True):
        if student_msg.strip():
            st.session_state[history_key].append({"role": "student", "content": student_msg.strip()})
            db.save_chat_message(st.session_state.current_student, "student", student_msg.strip(), selected_wq["id"])
            with st.spinner("🧑‍🏫 AI 老师思考中..."):
                try:
                    hint_key = f"hint_lv_{selected_wq['id']}"
                    lv = st.session_state.get(hint_key, 0)
                    reply = generate_tutor_message(
                        selected_wq["question_text"], selected_wq["student_answer"],
                        selected_wq["correct_answer"], selected_wq["error_type"],
                        selected_wq["knowledge_point"], selected_wq["analysis"],
                        st.session_state[history_key][:-1], student_msg.strip(), lv,
                    )
                    st.session_state[history_key].append({"role": "assistant", "content": reply})
                    db.save_chat_message(st.session_state.current_student, "assistant", reply, selected_wq["id"])
                    st.session_state[hint_key] = 0
                    st.rerun()
                except Exception as e:
                    st.error(f"生成失败：{e}")

    if c_stuck.button("🆘 我卡住了", use_container_width=True):
        hint_key = f"hint_lv_{selected_wq['id']}"
        st.session_state[hint_key] = st.session_state.get(hint_key, 0) + 1
        st.session_state[history_key].append({"role": "student", "content": "老师，我卡住了，想不出来... 😣"})
        with st.spinner("🧑‍🏫 给出更多提示..."):
            try:
                reply = generate_tutor_message(
                    selected_wq["question_text"], selected_wq["student_answer"],
                    selected_wq["correct_answer"], selected_wq["error_type"],
                    selected_wq["knowledge_point"], selected_wq["analysis"],
                    st.session_state[history_key][:-1],
                    "老师，我卡住了，想不出来...", st.session_state[hint_key],
                )
                st.session_state[history_key].append({"role": "assistant", "content": reply})
                db.save_chat_message(st.session_state.current_student, "assistant", reply, selected_wq["id"])
                st.rerun()
            except Exception as e:
                st.error(f"生成失败：{e}")

    if c_clear.button("🔄 重新开始", use_container_width=True):
        st.session_state[history_key] = []
        st.rerun()


# ══════════════════════════════════════════════════════════════
#  ✍️ 作文批改
# ══════════════════════════════════════════════════════════════

def render_essay():
    st.markdown('<div class="section-title">✍️ 作文批改</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        essay_lang = st.radio("作文语言", ["英语", "语文"], key="essay_lang", horizontal=True)
    with c2:
        essay_grade = st.selectbox("学生年级", GRADES, key="essay_grade")

    essay_img = st.file_uploader("📸 上传作文图片（可选，AI 自动识别）",
                                  type=["jpg", "jpeg", "png", "webp"], key="essay_img")
    if essay_img:
        st.image(Image.open(essay_img), use_column_width=True)

    essay_text = st.text_area("或直接粘贴作文文字", key="essay_text", height=200,
                               placeholder="把作文内容粘贴到这里...")

    if st.button("📝 开始批改", type="primary", use_container_width=True):
        text = essay_text.strip()
        if not text and essay_img:
            ensure_uploads_dir()
            ext = os.path.splitext(essay_img.name)[1]
            img_path = os.path.join(UPLOAD_DIR, f"essay_{uuid.uuid4()}{ext}")
            with open(img_path, "wb") as f:
                f.write(essay_img.getbuffer())
            with st.spinner("🔍 识别作文内容..."):
                try:
                    from agent.ocr import recognize_question
                    ocr = recognize_question(img_path, "这是作文，请完整识别全文")
                    text = ocr.get("question_text", "")
                except Exception as e:
                    st.error(f"识别失败：{e}")
                    return

        if not text:
            st.warning("请上传图片或粘贴文字")
            return

        with st.spinner("✍️ AI 批改中..."):
            try:
                if essay_lang == "英语":
                    result = correct_essay(text, essay_grade)
                else:
                    result = correct_chinese_essay(text, essay_grade)
                st.session_state.essay_result = result
                st.session_state.essay_source = text
                st.balloons()
            except Exception as e:
                st.error(f"批改失败：{e}")
                return

    if st.session_state.get("essay_result"):
        r = st.session_state.essay_result
        st.markdown("---")
        score = r.get("overall_score", 0)
        score_color = "#81B29A" if score >= 85 else ("#F4A261" if score >= 70 else "#E07A5F")

        c_s1, c_s2 = st.columns([1, 2])
        with c_s1:
            st.markdown(f"""
            <div class="warm-card" style="text-align:center;border-left:4px solid {score_color};">
                <div style="font-size:0.9rem;color:#6B7280;">综合评分</div>
                <div style="font-size:3rem;font-weight:800;color:{score_color};">{score}</div>
                <div style="font-size:0.8rem;color:#6B7280;">/ 100</div>
            </div>
            """, unsafe_allow_html=True)
        with c_s2:
            st.markdown(f"""
            <div class="warm-card">
                <div style="font-size:0.9rem;color:#6B7280;margin-bottom:6px;">💬 总评</div>
                <div style="line-height:1.8;">{r.get('comment', '')}</div>
            </div>
            """, unsafe_allow_html=True)

        col_good, col_bad = st.columns(2)
        with col_good:
            st.markdown("### ✨ 亮点")
            for s in r.get("strengths", []):
                st.markdown(f"- ✅ {s}")
        with col_bad:
            st.markdown("### 🎯 待改进")
            for w in r.get("weaknesses", []):
                st.markdown(f"- ⚠️ {w}")

        errors = r.get("errors", [])
        if errors:
            st.markdown("### 📝 逐处批改")
            for i, err in enumerate(errors):
                st.markdown(f"""
                <div class="warm-card" style="border-left:4px solid #E07A5F;padding:16px 20px;">
                    <span style="background:#FFEBEE;color:#E07A5F;padding:2px 10px;border-radius:8px;font-size:0.75rem;font-weight:600;">{err.get('type', '')}</span>
                    <div style="margin-top:8px;line-height:1.8;">
                        <span style="color:#C62828;text-decoration:line-through;">{err.get('original', '')}</span>
                        →
                        <span style="color:#2D6A4F;font-weight:600;">{err.get('correction', '')}</span>
                    </div>
                    <div style="color:#6B7280;font-size:0.85rem;margin-top:4px;">💡 {err.get('explanation', '')}</div>
                </div>
                """, unsafe_allow_html=True)

        with st.expander("📖 查看润色版范文"):
            st.write(r.get("polished_version", ""))


# ══════════════════════════════════════════════════════════════
#  📔 笔记整理
# ══════════════════════════════════════════════════════════════

def render_notes():
    st.markdown('<div class="section-title">📔 笔记整理</div>', unsafe_allow_html=True)
    st.markdown("把课后随手记的零散内容（或语音转写文字）交给 AI，整理成结构化教学笔记")

    raw_text = st.text_area(
        "🎤 粘贴零散记录",
        key="notes_raw", height=180,
        placeholder="例：今天小明状态不错 方程讲了配方法 还是不熟判别式 "
                    "作业P47做到8题 下次先把上次卷子错题过一遍 妈妈说周三要请假...",
    )

    if st.button("✨ AI 整理笔记", type="primary", use_container_width=True):
        if not raw_text.strip():
            st.warning("请先粘贴内容")
            return
        with st.spinner("📔 AI 整理中..."):
            try:
                note = organize_notes(raw_text.strip())
                st.session_state.organized_note = note
                st.balloons()
            except Exception as e:
                st.error(f"整理失败：{e}")

    if st.session_state.get("organized_note"):
        st.markdown("---")
        st.markdown(
            '<div class="warm-card" style="border-left:4px solid #7C3AED;">',
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state.organized_note)
        st.markdown("</div>", unsafe_allow_html=True)

        # 存入资料库
        st.markdown("### 💾 存入资料库")
        c1, c2, c3 = st.columns(3)
        with c1:
            sv_subj = st.selectbox("学科", SUBJECTS + ["语文"], key="note_sv_subj")
        with c2:
            sv_grade = st.selectbox("年级", ["通用"] + GRADES, key="note_sv_grade")
        with c3:
            sv_title = st.text_input("笔记标题", key="note_sv_title",
                                      placeholder="如：小明 8/18 课后记录")
        if st.button("💾 保存为资料（分类：笔记）", key="note_save", use_container_width=True):
            title = sv_title.strip() or "未命名笔记"
            db.add_material(sv_subj, title,
                            content=st.session_state.organized_note,
                            grade=sv_grade, category="笔记")
            st.success(f"🎉 已保存到资料库：{title}")
            st.rerun()

        st.download_button(
            "📥 下载笔记（Markdown）",
            data=st.session_state.organized_note,
            file_name="教学笔记.md",
            mime="text/markdown",
        )


# ══════════════════════════════════════════════════════════════
#  📖 课程日志
# ══════════════════════════════════════════════════════════════

def render_course_log():
    if not st.session_state.current_student:
        st.info("👈 请先在左侧选择一位学生（避免串数据）")
        return
    student = db.get_student(st.session_state.current_student)
    st.markdown('<div class="section-title">📖 课程日志</div>', unsafe_allow_html=True)
    st.markdown(f"当前学生：**{student['name']}**（课时费 ¥{student.get('hourly_rate', 0) or 0}/课时）")

    # 新增课程记录
    with st.expander("➕ 记录一节课", expanded=True):
        from datetime import datetime
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            cr_date = st.date_input("📅 日期", datetime.now(), key="cr_date")
        with c2:
            cr_subject = st.selectbox("📘 科目", SUBJECTS, key="cr_subj")
        with c3:
            cr_start = st.time_input("开始时间", datetime.now().replace(hour=19, minute=0), key="cr_start")
        with c4:
            cr_end = st.time_input("结束时间", datetime.now().replace(hour=21, minute=0), key="cr_end")

        cr_content = st.text_area("📝 上课内容（知识点摘要）", key="cr_content", height=80,
                                   placeholder="如：讲解一元二次方程求根公式，完成课本P45例题...")
        c5, c6 = st.columns(2)
        with c5:
            cr_homework = st.text_area("📋 课后作业", key="cr_homework", height=60)
        with c6:
            cr_mastery = st.selectbox("✅ 掌握情况", ["已掌握", "部分掌握", "未掌握"], key="cr_mastery")

        cr_plan = st.text_input("🎯 下次课计划", key="cr_plan", placeholder="如：继续练习判别式题型")
        cr_income = st.number_input("💰 课时收入（元）", min_value=0.0,
                                     value=float(student.get("hourly_rate", 0) or 0),
                                     step=50.0, key="cr_income")

        if st.button("💾 保存课程记录", type="primary", use_container_width=True):
            db.add_course_record(
                student_id=st.session_state.current_student,
                subject=cr_subject,
                date=str(cr_date),
                start_time=str(cr_start),
                end_time=str(cr_end),
                content=cr_content.strip(),
                homework=cr_homework.strip(),
                mastery=cr_mastery,
                plan_next=cr_plan.strip(),
                income=cr_income,
            )
            st.success("🎉 课程记录已保存")
            st.rerun()

    # 历史记录
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 📚 历史课程记录")
    records = db.list_course_records(student_id=st.session_state.current_student)

    if not records:
        st.info("暂无课程记录")
        return

    mastery_color = {"已掌握": "#81B29A", "部分掌握": "#F4A261", "未掌握": "#E07A5F"}
    for r in records:
        m_color = mastery_color.get(r.get("mastery", ""), "#6B7280")
        with st.expander(f"📅 {r['date']} · {r['subject']} · ¥{r['income']:,.0f}"):
            st.markdown(f"""
            <div class="warm-card">
                <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
                    <span style="background:#FFF0E0;color:#E76F51;padding:2px 10px;border-radius:8px;font-size:0.8rem;">👤 {r.get('student_name', '')}</span>
                    <span style="background:#E3F2FD;color:#457B9D;padding:2px 10px;border-radius:8px;font-size:0.8rem;">📘 {r['subject']}</span>
                    <span style="background:{m_color}22;color:{m_color};padding:2px 10px;border-radius:8px;font-size:0.8rem;">✅ {r.get('mastery', '未记录')}</span>
                    <span style="background:#E8F5E9;color:#2D6A4F;padding:2px 10px;border-radius:8px;font-size:0.8rem;">💰 ¥{r['income']:,.0f}</span>
                </div>
                <div style="line-height:1.8;">
                    <div><strong>📝 上课内容：</strong>{r.get('content', '') or '—'}</div>
                    <div><strong>📋 课后作业：</strong>{r.get('homework', '') or '—'}</div>
                    <div><strong>🎯 下次课计划：</strong>{r.get('plan_next', '') or '—'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  📅 周课表
# ══════════════════════════════════════════════════════════════

def render_schedule():
    st.markdown('<div class="section-title">📅 周课表</div>', unsafe_allow_html=True)

    records = db.get_weekly_schedule()
    if not records:
        st.info("📅 本周暂无课程安排，去「课程日志」添加课程吧～")
        return

    from datetime import datetime, timedelta
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    # 按日期分组
    by_date = {}
    for r in records:
        by_date.setdefault(r["date"], []).append(r)

    today_str = today.strftime("%Y-%m-%d")

    # 生成 HTML 周视图表格
    html = '<table class="schedule-table"><tr>'
    for i, wd in enumerate(weekdays):
        is_today = dates[i] == today_str
        badge = ' 🔆' if is_today else ''
        html += f'<th>{wd}{badge}<br><span style="font-size:0.7rem;opacity:0.8;">{dates[i][5:]}</span></th>'
    html += '</tr><tr>'

    for i, d in enumerate(dates):
        lessons = by_date.get(d, [])
        cell = ""
        for l in lessons:
            time_str = l.get("start_time", "")[:5] if l.get("start_time") else ""
            cell += f'<div class="schedule-lesson">🕒{time_str}<br>{l["student_name"]}<br>{l["subject"]}</div>'
        if not cell:
            cell = '<div style="color:#D1D5DB;text-align:center;padding:20px 0;">—</div>'
        is_today = d == today_str
        bg = "#FFF8F0" if is_today else "#FFFFFF"
        html += f'<td style="background:{bg};">{cell}</td>'

    html += '</tr></table>'
    st.markdown(html, unsafe_allow_html=True)

    st.markdown(f"💡 共 **{len(records)}** 节课 · 🔆 标记为今天")


# ══════════════════════════════════════════════════════════════
#  💰 收入统计
# ══════════════════════════════════════════════════════════════

def render_income():
    st.markdown('<div class="section-title">💰 收入统计</div>', unsafe_allow_html=True)

    from datetime import datetime
    months = []
    now = datetime.now()
    for i in range(6):
        m = now.year * 12 + now.month - 1 - i
        months.append(f"{m // 12}-{m % 12 + 1:02d}")

    sel_month = st.selectbox("选择月份", months, index=0, key="income_month")
    month_stats = db.get_monthly_income(month=sel_month)
    all_stats = db.get_monthly_income()

    c1, c2, c3, c4 = st.columns(4)
    render_metric_card(c1, "📅", f"{sel_month} 课程数", month_stats["lesson_count"])
    render_metric_card(c2, "💰", f"{sel_month} 收入", f"¥{month_stats['total']:,.0f}", color="#81B29A")
    render_metric_card(c3, "📚", "累计课程", all_stats["lesson_count"], color="#457B9D")
    render_metric_card(c4, "🏦", "累计收入", f"¥{all_stats['total']:,.0f}", color="#E07A5F")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 👤 按学生统计")

    by_student = db.get_income_by_student(month=sel_month)
    by_student = [s for s in by_student if s["lesson_count"] > 0]

    if not by_student:
        st.info(f"{sel_month} 暂无收入记录")
        return

    max_income = max(s["total_income"] for s in by_student)
    for s in by_student:
        pct = int(s["total_income"] / max(max_income, 1) * 100)
        st.markdown(f"""
        <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-weight:600;color:#264653;">{s['name']}</span>
                <span style="color:#2D6A4F;font-weight:700;">¥{s['total_income']:,.0f} · {s['lesson_count']}课</span>
            </div>
            <div style="background:#F0E6D8;border-radius:8px;height:12px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#81B29A,#2A9D8F);border-radius:8px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.warning("⚠️ 请记得核对实际收款情况，系统统计仅供参考")


# ══════════════════════════════════════════════════════════════
#  📁 资料库
# ══════════════════════════════════════════════════════════════

def render_materials():
    st.markdown('<div class="section-title">📁 资料库</div>', unsafe_allow_html=True)

    MATERIAL_CATEGORIES = ["课件", "习题", "试卷", "笔记", "链接", "其他"]

    with st.expander("➕ 添加资料", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            m_subj = st.selectbox("学科", SUBJECTS + ["语文"], key="mat_subj")
        with c2:
            m_grade = st.selectbox("年级", ["通用"] + GRADES, key="mat_grade")
        with c3:
            m_cat = st.selectbox("分类", MATERIAL_CATEGORIES, key="mat_cat")

        m_title = st.text_input("标题", key="mat_title", placeholder="如：初二上学期数学期中复习提纲")

        tab_text, tab_link = st.tabs(["📝 文字/笔记", "🔗 链接"])
        with tab_text:
            m_content = st.text_area("内容（Markdown）", key="mat_content", height=120)
        with tab_link:
            m_link = st.text_input("链接 URL", key="mat_link", placeholder="https://...")

        if st.button("💾 保存资料", key="mat_save", type="primary", use_container_width=True):
            if m_title.strip():
                db.add_material(m_subj, m_title.strip(), content=m_content.strip(),
                                link=m_link.strip(), grade=m_grade, category=m_cat)
                st.success("🎉 资料已保存")
                st.rerun()
            else:
                st.warning("请填写标题")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 筛选
    c1, c2, c3 = st.columns(3)
    with c1:
        f_subj = st.selectbox("筛选学科", ["全部"] + SUBJECTS + ["语文"], key="f_subj")
    with c2:
        f_grade = st.selectbox("筛选年级", ["全部", "通用"] + GRADES, key="f_grade")
    with c3:
        f_cat = st.selectbox("筛选分类", ["全部"] + MATERIAL_CATEGORIES, key="f_cat")

    materials = db.list_materials(
        subject=None if f_subj == "全部" else f_subj,
        grade=None if f_grade == "全部" else f_grade,
        category=None if f_cat == "全部" else f_cat,
    )

    if not materials:
        st.info("📭 暂无资料，点击上方「添加资料」")
        return

    cat_emoji = {"课件": "📑", "习题": "✏️", "试卷": "📄", "笔记": "📔", "链接": "🔗", "其他": "📌"}
    for m in materials:
        title_line = f"{cat_emoji.get(m['category'], '📌')} {m['title']}"
        with st.expander(title_line):
            st.markdown(f"""
            <span style="background:#FFF0E0;color:#E76F51;padding:2px 10px;border-radius:8px;font-size:0.8rem;">{m['subject']}</span>
            <span style="background:#E3F2FD;color:#457B9D;padding:2px 10px;border-radius:8px;font-size:0.8rem;margin-left:4px;">{m.get('grade', '')}</span>
            <span style="background:#F3E8FF;color:#7C3AED;padding:2px 10px;border-radius:8px;font-size:0.8rem;margin-left:4px;">{m['category']}</span>
            """, unsafe_allow_html=True)
            if m.get("link"):
                st.markdown(f"🔗 [{m['link']}]({m['link']})")
            if m.get("content"):
                st.markdown(m["content"])
            if st.button("🗑️ 删除", key=f"del_{m['id']}"):
                db.delete_material(m["id"])
                st.rerun()


# ══════════════════════════════════════════════════════════════
#  📊 学情周报
# ══════════════════════════════════════════════════════════════

def render_report():
    if not st.session_state.current_student:
        st.info("👈 请先在左侧选择一位学生")
        return
    student = db.get_student(st.session_state.current_student)
    st.markdown('<div class="section-title">📊 学情周报</div>', unsafe_allow_html=True)
    st.markdown(f"为 **{student['name']}** 生成学习周报")

    weeks = st.slider("回溯几周", 1, 4, 1, key="report_weeks")

    if st.button("📄 生成周报", type="primary", use_container_width=True):
        with st.spinner("🤖 AI 正在生成周报..."):
            try:
                report = generate_weekly_report(st.session_state.current_student, weeks)
                st.session_state.weekly_report = report
                st.balloons()
            except Exception as e:
                st.error(f"生成失败：{e}")

    if st.session_state.get("weekly_report"):
        st.markdown("---")
        st.markdown('<div class="warm-card" style="border-left:4px solid #2A9D8F;">', unsafe_allow_html=True)
        st.markdown(st.session_state.weekly_report)
        st.markdown("</div>", unsafe_allow_html=True)
        st.download_button(
            "📥 下载周报（Markdown）",
            data=st.session_state.weekly_report,
            file_name=f"周报_{student['name']}.md",
            mime="text/markdown",
        )


# ══════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════

def main():
    page = render_sidebar()

    if page == "🏠 首页总览":
        render_dashboard()
    elif page == "📝 错题录入":
        render_wrong_question_input()
    elif page == "✏️ 变式练习":
        render_practice()
    elif page == "🗣️ 苏格拉底辅导":
        render_tutor()
    elif page == "✍️ 作文批改":
        render_essay()
    elif page == "📔 笔记整理":
        render_notes()
    elif page == "📖 课程日志":
        render_course_log()
    elif page == "📅 周课表":
        render_schedule()
    elif page == "💰 收入统计":
        render_income()
    elif page == "📁 资料库":
        render_materials()
    elif page == "📊 学情周报":
        render_report()


if __name__ == "__main__":
    main()
