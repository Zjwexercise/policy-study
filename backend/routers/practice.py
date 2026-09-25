import sqlite3
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
        COUNT(DISTINCT CASE WHEN up.is_starred = 1 THEN up.question_id END) as total_starred
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

    return {
        "overview": overview,
        "categories": categories
    }
