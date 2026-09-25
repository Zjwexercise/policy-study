import json
import sqlite3
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/api/wrong-book", tags=["wrong-book"])

class MasterWrongModel(BaseModel):
    is_mastered: bool

@router.get("")
def list_wrong_questions(
    workbook_id: Optional[int] = None,
    category: Optional[str] = None,
    include_mastered: bool = False,
    conn: sqlite3.Connection = Depends(get_db)
):
    cursor = conn.cursor()
    query = """
    SELECT 
        wb.id as wrong_id, wb.workbook_id, wb.question_id, wb.wrong_count, 
        wb.last_wrong_answer, wb.is_mastered, wb.updated_at as wrong_time,
        q.question_num, q.question_type, q.category, q.stem, q.options_json, 
        q.answer, q.explanation,
        w.name as workbook_name,
        up.is_starred,
        n.content as note_content
    FROM wrong_book wb
    JOIN questions q ON wb.question_id = q.id
    JOIN workbooks w ON wb.workbook_id = w.id
    LEFT JOIN user_progress up ON q.id = up.question_id
    LEFT JOIN notes n ON q.id = n.question_id
    WHERE 1=1
    """
    params = []

    if not include_mastered:
        query += " AND wb.is_mastered = 0"

    if workbook_id:
        query += " AND wb.workbook_id = ?"
        params.append(workbook_id)

    if category and category != "全部":
        query += " AND q.category = ?"
        params.append(category)

    query += " ORDER BY wb.wrong_count DESC, wb.updated_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        options = []
        try:
            options = json.loads(r["options_json"])
        except Exception:
            options = []

        results.append({
            "wrong_id": r["wrong_id"],
            "workbook_id": r["workbook_id"],
            "workbook_name": r["workbook_name"],
            "question_id": r["question_id"],
            "wrong_count": r["wrong_count"],
            "last_wrong_answer": r["last_wrong_answer"],
            "is_mastered": bool(r["is_mastered"]),
            "wrong_time": r["wrong_time"],
            "question_num": r["question_num"],
            "question_type": r["question_type"],
            "category": r["category"],
            "stem": r["stem"],
            "options": options,
            "answer": r["answer"],
            "explanation": r["explanation"],
            "is_starred": bool(r["is_starred"]) if r["is_starred"] is not None else False,
            "note_content": r["note_content"] or ""
        })

    return results

@router.post("/{question_id}/master")
def toggle_master_status(question_id: int, payload: MasterWrongModel, conn: sqlite3.Connection = Depends(get_db)):
    """标记为已掌握（移出错题本）或重新纳入错题本"""
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE wrong_book 
    SET is_mastered = ?, updated_at = CURRENT_TIMESTAMP
    WHERE question_id = ?
    """, (1 if payload.is_mastered else 0, question_id))
    conn.commit()

    return {"success": True, "is_mastered": payload.is_mastered}

@router.delete("/clear")
def clear_wrong_book(workbook_id: Optional[int] = None, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    if workbook_id:
        cursor.execute("DELETE FROM wrong_book WHERE workbook_id = ?", (workbook_id,))
    else:
        cursor.execute("DELETE FROM wrong_book")
    conn.commit()
    return {"success": True, "message": "错题记录已清空"}
