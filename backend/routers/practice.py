import sqlite3
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import get_db

router = APIRouter(prefix="/api/practice", tags=["practice"])

class SubmitAnswerModel(BaseModel):
    workbook_id: int
    question_id: int
    user_answer: str # e.g. "A" or "ABC"

class StarModel(BaseModel):
    workbook_id: int
    question_id: int
    is_starred: bool

class KillModel(BaseModel):
    workbook_id: int
    question_id: int
    is_killed: bool

class StudyTimeModel(BaseModel):
    seconds: int
    study_date: Optional[str] = None

def normalize_answer(ans: str) -> str:
    """去除空格并按字母顺序排序，例如 'BCA' -> 'ABC'"""
    if not ans:
        return ""
    clean = "".join([c.upper() for c in ans if c.isalpha()])
    return "".join(sorted(clean))

@router.post("/submit")
def submit_answer(payload: SubmitAnswerModel, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT q.id, q.workbook_id, q.answer, q.explanation, q.question_type 
        FROM questions q 
        WHERE q.id = ? AND q.workbook_id = ?
    """, (payload.question_id, payload.workbook_id))
    q = cursor.fetchone()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    correct_answer = normalize_answer(q["answer"])
    user_ans_norm = normalize_answer(payload.user_answer)
    is_correct = 1 if user_ans_norm == correct_answer else 0

    # 1. 保存/更新 user_progress
    cursor.execute("""
        INSERT INTO user_progress (workbook_id, question_id, user_answer, is_correct)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(workbook_id, question_id) DO UPDATE SET
            user_answer = excluded.user_answer,
            is_correct = excluded.is_correct,
            answered_at = CURRENT_TIMESTAMP
    """, (payload.workbook_id, payload.question_id, user_ans_norm, is_correct))

    # 2. 如果答错，自动加入或更新错题本
    if not is_correct:
        cursor.execute("""
            INSERT INTO wrong_book (workbook_id, question_id, wrong_count, last_wrong_answer, is_mastered)
            VALUES (?, ?, 1, ?, 0)
            ON CONFLICT(workbook_id, question_id) DO UPDATE SET
                wrong_count = wrong_book.wrong_count + 1,
                last_wrong_answer = excluded.last_wrong_answer,
                is_mastered = 0,
                updated_at = CURRENT_TIMESTAMP
        """, (payload.workbook_id, payload.question_id, user_ans_norm))
    else:
        # 如果答对了，且之前在错题本中，可以保持记录或便于在错题本中查看掌握情况
        pass

    conn.commit()

    return {
        "success": True,
        "is_correct": bool(is_correct),
        "user_answer": user_ans_norm,
        "correct_answer": correct_answer,
        "explanation": q["explanation"]
    }

@router.post("/star")
def toggle_star(payload: StarModel, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_progress (workbook_id, question_id, is_starred)
        VALUES (?, ?, ?)
        ON CONFLICT(workbook_id, question_id) DO UPDATE SET
            is_starred = excluded.is_starred
    """, (payload.workbook_id, payload.question_id, 1 if payload.is_starred else 0))
    conn.commit()

    return {"success": True, "is_starred": payload.is_starred}

@router.post("/kill")
def toggle_kill(payload: KillModel, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_progress (workbook_id, question_id, is_killed)
        VALUES (?, ?, ?)
        ON CONFLICT(workbook_id, question_id) DO UPDATE SET
            is_killed = excluded.is_killed
    """, (payload.workbook_id, payload.question_id, 1 if payload.is_killed else 0))
    conn.commit()
    return {"success": True, "is_killed": payload.is_killed}

@router.post("/study-time")
def report_study_time(payload: StudyTimeModel, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    date_str = payload.study_date or datetime.now().strftime("%Y-%m-%d")
    sec = max(1, min(payload.seconds, 7200)) # 限制单次合理步进
    cursor.execute("""
        INSERT INTO study_logs (study_date, duration_seconds)
        VALUES (?, ?)
        ON CONFLICT(study_date) DO UPDATE SET
            duration_seconds = study_logs.duration_seconds + excluded.duration_seconds,
            updated_at = CURRENT_TIMESTAMP
    """, (date_str, sec))
    conn.commit()
    return {"success": True, "date": date_str, "logged_seconds": sec}

@router.get("/stats")
def get_global_stats(conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    
    # 总体统计
    cursor.execute("""
    SELECT 
        COUNT(DISTINCT q.id) as total_questions,
        COUNT(DISTINCT up.question_id) as total_answered,
        SUM(CASE WHEN up.is_correct = 1 THEN 1 ELSE 0 END) as total_correct,
        COUNT(DISTINCT wb.question_id) as total_wrong,
        COUNT(DISTINCT n.question_id) as total_notes,
        COUNT(DISTINCT CASE WHEN up.is_starred = 1 THEN up.question_id END) as total_starred,
        COUNT(DISTINCT CASE WHEN up.is_killed = 1 THEN up.question_id END) as total_killed
    FROM questions q
    LEFT JOIN user_progress up ON q.id = up.question_id
    LEFT JOIN wrong_book wb ON q.id = wb.question_id AND wb.is_mastered = 0
    LEFT JOIN notes n ON q.id = n.question_id
    """)
    overview = dict(cursor.fetchone())

    # 按政治学科分类统计
    cursor.execute("""
    SELECT 
        q.category,
        COUNT(q.id) as total,
        COUNT(up.question_id) as answered,
        SUM(CASE WHEN up.is_correct = 1 THEN 1 ELSE 0 END) as correct
    FROM questions q
    LEFT JOIN user_progress up ON q.id = up.question_id
    GROUP BY q.category
    """)
    category_rows = cursor.fetchall()
    categories = []
    for r in category_rows:
        total = r["total"] or 0
        answered = r["answered"] or 0
        correct = r["correct"] or 0
        acc = round((correct / answered * 100), 1) if answered > 0 else 0
        categories.append({
            "category": r["category"],
            "total": total,
            "answered": answered,
            "correct": correct,
            "accuracy": acc
        })

    # 每日刷题量与学习时长趋势（过去 30 天）
    today = datetime.now().date()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]

    # 获取每日刷题答对答错数据
    cursor.execute("""
        SELECT 
            date(answered_at) as day,
            COUNT(*) as total,
            SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as wrong
        FROM user_progress
        WHERE answered_at IS NOT NULL
        GROUP BY date(answered_at)
    """)
    q_by_day = {r["day"]: dict(r) for r in cursor.fetchall()}

    # 获取每日记录的学习时长
    cursor.execute("SELECT study_date, duration_seconds FROM study_logs")
    s_by_day = {r["study_date"]: r["duration_seconds"] for r in cursor.fetchall()}

    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    daily_trends = []
    today_str = today.strftime("%Y-%m-%d")

    for d_str in dates:
        d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
        q_data = q_by_day.get(d_str, {})
        answered = q_data.get("total", 0)
        correct = q_data.get("correct", 0)
        wrong = q_data.get("wrong", 0)
        acc = round((correct / answered * 100), 1) if answered > 0 else 0
        
        duration = s_by_day.get(d_str, 0)
        # 若之前做过题但未记时长，按单题 50 秒补充合理基准
        if duration == 0 and answered > 0:
            duration = answered * 50
        
        daily_trends.append({
            "date": d_str,
            "display_date": d_str[5:], # "11-09"
            "day_name": weekday_names[d_obj.weekday()],
            "answered": answered,
            "correct": correct,
            "wrong": wrong,
            "accuracy": acc,
            "study_seconds": duration,
            "study_minutes": round(duration / 60, 1)
        })

    # 计算总学习时长与今日学习时长
    cursor.execute("SELECT SUM(duration_seconds) FROM study_logs")
    db_total_sec = cursor.fetchone()[0] or 0
    total_study_seconds = max(db_total_sec, sum(d["study_seconds"] for d in daily_trends))
    today_study_seconds = next((d["study_seconds"] for d in daily_trends if d["date"] == today_str), 0)
    today_answered = next((d["answered"] for d in daily_trends if d["date"] == today_str), 0)

    overview["total_study_seconds"] = total_study_seconds
    overview["today_study_seconds"] = today_study_seconds
    overview["today_answered"] = today_answered

    return {
        "overview": overview,
        "categories": categories,
        "daily_trends": daily_trends
    }
