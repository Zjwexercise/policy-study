import json
import sqlite3
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/api", tags=["questions"])

class QuestionUpdateModel(BaseModel):
    stem: str
    options: List[Dict[str, str]]
    answer: str
    explanation: Optional[str] = ""
    category: Optional[str] = "综合"
    question_type: Optional[str] = "single"

@router.get("/workbooks/{workbook_id}/questions")
def get_workbook_questions(
    workbook_id: str,
    category: Optional[str] = None,
    question_type: Optional[str] = None,
    status: Optional[str] = "all", # all, unattempted, wrong, correct, starred
    conn: sqlite3.Connection = Depends(get_db)
):
    cursor = conn.cursor()
    is_all = str(workbook_id).lower() in ["all", "0", "-1"]
    
    query = """
    SELECT 
        q.id, q.workbook_id, q.question_num, q.question_type, q.category, 
        q.stem, q.options_json, q.answer, q.explanation, q.order_num,
        w.name as workbook_name,
        up.user_answer, up.is_correct, up.is_starred,
        wb.wrong_count, wb.is_mastered,
        n.content as note_content
    FROM questions q
    JOIN workbooks w ON q.workbook_id = w.id
    LEFT JOIN user_progress up ON q.id = up.question_id
    LEFT JOIN wrong_book wb ON q.id = wb.question_id
    LEFT JOIN notes n ON q.id = n.question_id
    WHERE 1=1
    """
    params = []

    if not is_all:
        query += " AND q.workbook_id = ?"
        params.append(int(workbook_id))

    if category and category != "全部":
        query += " AND q.category = ?"
        params.append(category)

    if question_type and question_type != "全部":
        query += " AND q.question_type = ?"
        params.append(question_type)

    if status == "unattempted":
        query += " AND up.user_answer IS NULL"
    elif status == "wrong":
        query += " AND wb.id IS NOT NULL AND wb.is_mastered = 0"
    elif status == "correct":
        query += " AND up.is_correct = 1"
    elif status == "starred":
        query += " AND up.is_starred = 1"

    if is_all:
        query += " ORDER BY q.workbook_id ASC, q.order_num ASC, q.id ASC"
    else:
        query += " ORDER BY q.order_num ASC, q.id ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    questions = []
    for r in rows:
        options = []
        try:
            options = json.loads(r["options_json"])
        except Exception:
            options = []

        questions.append({
            "id": r["id"],
            "workbook_id": r["workbook_id"],
            "workbook_name": r["workbook_name"] if "workbook_name" in r.keys() else "",
            "question_num": r["question_num"],
            "question_type": r["question_type"],
            "category": r["category"],
            "stem": r["stem"],
            "options": options,
            "answer": r["answer"],
            "explanation": r["explanation"],
            "order_num": r["order_num"],
            "user_answer": r["user_answer"],
            "is_correct": bool(r["is_correct"]) if r["is_correct"] is not None else None,
            "is_starred": bool(r["is_starred"]) if r["is_starred"] is not None else False,
            "wrong_count": r["wrong_count"] or 0,
            "is_mastered": bool(r["is_mastered"]) if r["is_mastered"] is not None else False,
            "has_note": bool(r["note_content"]),
            "note_content": r["note_content"] or ""
        })

    return questions

@router.get("/questions/{question_id}")
def get_single_question(question_id: int, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        q.id, q.workbook_id, q.question_num, q.question_type, q.category, 
        q.stem, q.options_json, q.answer, q.explanation, q.order_num,
        up.user_answer, up.is_correct, up.is_starred,
        n.content as note_content
    FROM questions q
    LEFT JOIN user_progress up ON q.id = up.question_id
    LEFT JOIN notes n ON q.id = n.question_id
    WHERE q.id = ?
    """, (question_id,))
    r = cursor.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="题目不存在")

    try:
        options = json.loads(r["options_json"])
    except Exception:
        options = []

    return {
        "id": r["id"],
        "workbook_id": r["workbook_id"],
        "question_num": r["question_num"],
        "question_type": r["question_type"],
        "category": r["category"],
        "stem": r["stem"],
        "options": options,
        "answer": r["answer"],
        "explanation": r["explanation"],
        "user_answer": r["user_answer"],
        "is_correct": bool(r["is_correct"]) if r["is_correct"] is not None else None,
        "is_starred": bool(r["is_starred"]) if r["is_starred"] is not None else False,
        "note_content": r["note_content"] or ""
    }

@router.put("/questions/{question_id}")
def update_question(question_id: int, payload: QuestionUpdateModel, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="题目不存在")

    cursor.execute("""
    UPDATE questions 
    SET stem = ?, options_json = ?, answer = ?, explanation = ?, category = ?, question_type = ?
    WHERE id = ?
    """, (
        payload.stem,
        json.dumps(payload.options, ensure_ascii=False),
        payload.answer.strip().upper(),
        payload.explanation or "",
        payload.category or "综合",
        payload.question_type or "single",
        question_id
    ))
    conn.commit()

    return {"success": True, "message": "题目修改已保存"}
