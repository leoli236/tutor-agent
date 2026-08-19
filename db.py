"""
数据库层 —— 使用 SQLite 持久化学生、错题、练习、对话记录、课程日志、资料库

数据模型:
  students          学生信息（含课时费）
  wrong_questions   错题录入（含归因结果）
  practice_problems  变式练习题
  practice_sessions  学生答题会话
  chat_messages      苏格拉底辅导对话记录
  course_records     课程日志（每节课记录）
  materials          资料库（按学科×年级分类）
  income_records     课时收入记录
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta

from config import DB_PATH


def get_db():
    """获取数据库连接（自动创建/迁移表）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_tables(conn)
    return conn


def _init_tables(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        grade       TEXT,
        subjects    TEXT DEFAULT '[]',
        hourly_rate REAL DEFAULT 0,
        notes       TEXT DEFAULT '',
        created_at  TEXT DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS wrong_questions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id      INTEGER NOT NULL REFERENCES students(id),
        subject         TEXT NOT NULL,
        image_path      TEXT,
        question_text   TEXT,
        student_answer  TEXT,
        correct_answer  TEXT,
        error_type      TEXT,
        knowledge_point TEXT,
        analysis        TEXT,
        difficulty       TEXT DEFAULT '中等',
        created_at      TEXT DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS practice_problems (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        wrong_question_id  INTEGER NOT NULL REFERENCES wrong_questions(id),
        problem_text    TEXT NOT NULL,
        answer          TEXT,
        hint            TEXT,
        difficulty      TEXT DEFAULT '中等',
        created_at      TEXT DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS practice_sessions (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        practice_problem_id INTEGER NOT NULL REFERENCES practice_problems(id),
        student_id          INTEGER NOT NULL REFERENCES students(id),
        student_answer      TEXT,
        is_correct          INTEGER DEFAULT 0,
        hints_used          INTEGER DEFAULT 0,
        tutor_messages      TEXT DEFAULT '[]',
        created_at          TEXT DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id      INTEGER NOT NULL REFERENCES students(id),
        wrong_question_id INTEGER REFERENCES wrong_questions(id),
        role            TEXT NOT NULL,
        content         TEXT NOT NULL,
        created_at      TEXT DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS course_records (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  INTEGER NOT NULL REFERENCES students(id),
        subject     TEXT NOT NULL,
        date        TEXT NOT NULL,
        start_time  TEXT DEFAULT '',
        end_time    TEXT DEFAULT '',
        content     TEXT DEFAULT '',
        homework    TEXT DEFAULT '',
        mastery     TEXT DEFAULT '',
        plan_next   TEXT DEFAULT '',
        income      REAL DEFAULT 0,
        notes       TEXT DEFAULT '',
        created_at  TEXT DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS materials (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        subject     TEXT NOT NULL,
        grade       TEXT DEFAULT '',
        title       TEXT NOT NULL,
        content     TEXT DEFAULT '',
        file_path   TEXT DEFAULT '',
        link        TEXT DEFAULT '',
        category    TEXT DEFAULT '课件',
        tags        TEXT DEFAULT '[]',
        created_at  TEXT DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 兼容迁移：如果 hourly_rate 列不存在则添加
    try:
        conn.execute("SELECT hourly_rate FROM students LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE students ADD COLUMN hourly_rate REAL DEFAULT 0")


# ── 学生 CRUD ──────────────────────────────────────────────────

def add_student(name, grade="", subjects=None, hourly_rate=0, notes=""):
    db = get_db()
    cur = db.execute(
        "INSERT INTO students (name, grade, subjects, hourly_rate, notes) VALUES (?,?,?,?,?)",
        (name, grade, json.dumps(subjects or [], ensure_ascii=False), hourly_rate, notes),
    )
    db.commit()
    student_id = cur.lastrowid
    db.close()
    return student_id


def list_students():
    db = get_db()
    rows = db.execute("SELECT * FROM students ORDER BY created_at DESC").fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_student(student_id):
    db = get_db()
    row = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    db.close()
    return dict(row) if row else None


def update_student(student_id, **kwargs):
    """更新学生信息（支持任意字段）"""
    allowed = {"name", "grade", "subjects", "hourly_rate", "notes"}
    sets = []
    vals = []
    for k, v in kwargs.items():
        if k in allowed:
            if k == "subjects" and isinstance(v, list):
                v = json.dumps(v, ensure_ascii=False)
            sets.append(f"{k} = ?")
            vals.append(v)
    if not sets:
        return
    vals.append(student_id)
    db = get_db()
    db.execute(f"UPDATE students SET {', '.join(sets)} WHERE id = ?", vals)
    db.commit()
    db.close()


# ── 错题 CRUD ──────────────────────────────────────────────────

def add_wrong_question(student_id, subject, question_text, student_answer="",
                       correct_answer="", error_type="", knowledge_point="",
                       analysis="", image_path="", difficulty="中等"):
    db = get_db()
    cur = db.execute(
        """INSERT INTO wrong_questions
           (student_id, subject, image_path, question_text, student_answer,
            correct_answer, error_type, knowledge_point, analysis, difficulty)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (student_id, subject, image_path, question_text, student_answer,
         correct_answer, error_type, knowledge_point, analysis, difficulty),
    )
    db.commit()
    qid = cur.lastrowid
    db.close()
    return qid


def list_wrong_questions(student_id=None, subject=None):
    db = get_db()
    sql = "SELECT wq.*, s.name as student_name FROM wrong_questions wq JOIN students s ON wq.student_id = s.id WHERE 1=1"
    params = []
    if student_id:
        sql += " AND wq.student_id = ?"
        params.append(student_id)
    if subject:
        sql += " AND wq.subject = ?"
        params.append(subject)
    sql += " ORDER BY wq.created_at DESC"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_wrong_question(qid):
    db = get_db()
    row = db.execute("SELECT * FROM wrong_questions WHERE id = ?", (qid,)).fetchone()
    db.close()
    return dict(row) if row else None


# ── 练习题 CRUD ────────────────────────────────────────────────

def add_practice_problems(wrong_question_id, problems):
    db = get_db()
    ids = []
    for p in problems:
        cur = db.execute(
            """INSERT INTO practice_problems
               (wrong_question_id, problem_text, answer, hint, difficulty)
               VALUES (?,?,?,?,?)""",
            (wrong_question_id, p["problem_text"], p.get("answer", ""),
             p.get("hint", ""), p.get("difficulty", "中等")),
        )
        ids.append(cur.lastrowid)
    db.commit()
    db.close()
    return ids


def get_practice_problems(wrong_question_id):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM practice_problems WHERE wrong_question_id = ? ORDER BY id",
        (wrong_question_id,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── 练习会话 ───────────────────────────────────────────────────

def save_practice_session(practice_problem_id, student_id, student_answer,
                          is_correct, hints_used, tutor_messages=None):
    db = get_db()
    cur = db.execute(
        """INSERT INTO practice_sessions
           (practice_problem_id, student_id, student_answer, is_correct,
            hints_used, tutor_messages)
           VALUES (?,?,?,?,?,?)""",
        (practice_problem_id, student_id, student_answer,
         int(is_correct), hints_used,
         json.dumps(tutor_messages or [], ensure_ascii=False)),
    )
    db.commit()
    db.close()
    return cur.lastrowid


# ── 对话记录 ───────────────────────────────────────────────────

def save_chat_message(student_id, role, content, wrong_question_id=None):
    db = get_db()
    db.execute(
        """INSERT INTO chat_messages (student_id, wrong_question_id, role, content)
           VALUES (?, ?, ?, ?)""",
        (student_id, wrong_question_id, role, content),
    )
    db.commit()
    db.close()


def get_chat_history(student_id, wrong_question_id=None, limit=20):
    db = get_db()
    sql = "SELECT * FROM chat_messages WHERE student_id = ?"
    params = [student_id]
    if wrong_question_id:
        sql += " AND wrong_question_id = ?"
        params.append(wrong_question_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    rows = db.execute(sql, params + [limit]).fetchall()
    db.close()
    return [dict(r) for r in reversed(rows)]


# ── 课程日志 ───────────────────────────────────────────────────

def add_course_record(student_id, subject, date, start_time="", end_time="",
                      content="", homework="", mastery="", plan_next="",
                      income=0, notes=""):
    db = get_db()
    cur = db.execute(
        """INSERT INTO course_records
           (student_id, subject, date, start_time, end_time,
            content, homework, mastery, plan_next, income, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (student_id, subject, date, start_time, end_time,
         content, homework, mastery, plan_next, income, notes),
    )
    db.commit()
    db.close()
    return cur.lastrowid


def list_course_records(student_id=None, subject=None, month=None):
    db = get_db()
    sql = """SELECT cr.*, s.name as student_name
             FROM course_records cr JOIN students s ON cr.student_id = s.id
             WHERE 1=1"""
    params = []
    if student_id:
        sql += " AND cr.student_id = ?"
        params.append(student_id)
    if subject:
        sql += " AND cr.subject = ?"
        params.append(subject)
    if month:
        sql += " AND strftime('%Y-%m', cr.date) = ?"
        params.append(month)
    sql += " ORDER BY cr.date DESC, cr.start_time DESC"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_monthly_income(student_id=None, month=None):
    """获取月收入统计"""
    db = get_db()
    sql = """SELECT COALESCE(SUM(income), 0) as total,
                    COUNT(*) as lesson_count
             FROM course_records WHERE 1=1"""
    params = []
    if student_id:
        sql += " AND student_id = ?"
        params.append(student_id)
    if month:
        sql += " AND strftime('%Y-%m', date) = ?"
        params.append(month)
    row = db.execute(sql, params).fetchone()
    db.close()
    return dict(row)


def get_income_by_student(month=None):
    """按学生统计收入"""
    db = get_db()
    sql = """SELECT s.name, s.id, COALESCE(SUM(cr.income), 0) as total_income,
                    COUNT(cr.id) as lesson_count
             FROM students s
             LEFT JOIN course_records cr ON s.id = cr.student_id"""
    params = []
    if month:
        sql += " AND strftime('%Y-%m', cr.date) = ?"
        params.append(month)
    sql += " GROUP BY s.id ORDER BY total_income DESC"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_weekly_schedule(student_id=None):
    """获取本周课表"""
    db = get_db()
    # 获取本周一到周日的日期
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    sql = """SELECT cr.*, s.name as student_name
             FROM course_records cr JOIN students s ON cr.student_id = s.id
             WHERE cr.date IN (?,?,?,?,?,?,?)
             ORDER BY cr.date, cr.start_time"""
    params = dates
    if student_id:
        sql += " AND cr.student_id = ?"
        params.append(student_id)
    rows = db.execute(sql, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── 资料库 ─────────────────────────────────────────────────────

def add_material(subject, title, content="", file_path="", link="",
                 grade="", category="课件", tags=None):
    db = get_db()
    cur = db.execute(
        """INSERT INTO materials (subject, grade, title, content, file_path, link, category, tags)
           VALUES (?,?,?,?,?,?,?,?)""",
        (subject, grade, title, content, file_path, link, category,
         json.dumps(tags or [], ensure_ascii=False)),
    )
    db.commit()
    mid = cur.lastrowid
    db.close()
    return mid


def list_materials(subject=None, grade=None, category=None):
    db = get_db()
    sql = "SELECT * FROM materials WHERE 1=1"
    params = []
    if subject:
        sql += " AND subject = ?"
        params.append(subject)
    if grade:
        sql += " AND grade = ?"
        params.append(grade)
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY created_at DESC"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def delete_material(material_id):
    db = get_db()
    db.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    db.commit()
    db.close()


# ── 统计查询 ───────────────────────────────────────────────────

def get_student_stats(student_id):
    """获取学生的学习统计数据"""
    db = get_db()
    stats = {}

    rows = db.execute(
        "SELECT subject, COUNT(*) as cnt FROM wrong_questions WHERE student_id = ? GROUP BY subject",
        (student_id,),
    ).fetchall()
    stats["wrong_by_subject"] = {r["subject"]: r["cnt"] for r in rows}

    rows = db.execute(
        "SELECT error_type, COUNT(*) as cnt FROM wrong_questions WHERE student_id = ? GROUP BY error_type",
        (student_id,),
    ).fetchall()
    stats["error_type_dist"] = {r["error_type"]: r["cnt"] for r in rows}

    rows = db.execute(
        """SELECT knowledge_point, COUNT(*) as cnt
           FROM wrong_questions WHERE student_id = ? AND knowledge_point != ''
           GROUP BY knowledge_point ORDER BY cnt DESC LIMIT 10""",
        (student_id,),
    ).fetchall()
    stats["weak_points"] = [dict(r) for r in rows]

    row = db.execute(
        """SELECT COUNT(*) as total,
                  SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) as correct
           FROM practice_sessions ps
           JOIN practice_problems pp ON ps.practice_problem_id = pp.id
           JOIN wrong_questions wq ON pp.wrong_question_id = wq.id
           WHERE wq.student_id = ?""",
        (student_id,),
    ).fetchone()
    if row and row["total"] > 0:
        stats["practice_accuracy"] = round(row["correct"] / row["total"] * 100, 1)
        stats["practice_total"] = row["total"]
    else:
        stats["practice_accuracy"] = 0
        stats["practice_total"] = 0

    # 课程和收入统计
    row = db.execute(
        "SELECT COUNT(*) as cnt, COALESCE(SUM(income), 0) as total_income FROM course_records WHERE student_id = ?",
        (student_id,),
    ).fetchone()
    stats["total_lessons"] = row["cnt"]
    stats["total_income"] = row["total_income"]

    db.close()
    return stats
