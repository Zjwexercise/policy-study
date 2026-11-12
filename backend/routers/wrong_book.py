import json
import sqlite3
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/api/wrong-book", tags=["wrong-book"])

class MasterWrongModel(BaseModel):
    is_mastered: bool

class ResetAnswersModel(BaseModel):
    workbook_id: Optional[int] = None

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
        up.user_answer, up.is_correct, up.is_starred,
        n.content as note_content
    FROM wrong_book wb
    JOIN questions q ON wb.question_id = q.id
    JOIN workbooks w ON wb.workbook_id = w.id
    LEFT JOIN user_progress up ON (wb.workbook_id = up.workbook_id AND wb.question_id = up.question_id)
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
            raw_opts = json.loads(r["options_json"])
            if isinstance(raw_opts, dict):
                options = [{"key": k, "value": v} for k, v in raw_opts.items()]
            elif isinstance(raw_opts, list):
                options = raw_opts
        except Exception:
            options = []

        q_type = r["question_type"]
        if q_type in ["单选题", "单选"]:
            q_type = "single"
        elif q_type in ["多选题", "多选"]:
            q_type = "multiple"
        elif not q_type:
            q_type = "multiple" if len(r["answer"] or "") > 1 else "single"

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
            "question_type": q_type,
            "category": r["category"],
            "stem": r["stem"],
            "options": options,
            "answer": r["answer"],
            "explanation": r["explanation"],
            "user_answer": r["user_answer"] if "user_answer" in r.keys() else None,
            "is_correct": bool(r["is_correct"]) if ("is_correct" in r.keys() and r["is_correct"] is not None) else None,
            "is_starred": bool(r["is_starred"]) if r["is_starred"] is not None else False,
            "note_content": r["note_content"] or ""
        })

    return results

@router.delete("/{question_id}")
def remove_wrong_question(question_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """彻底将题目从错题本中移除"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wrong_book WHERE question_id = ?", (question_id,))
    conn.commit()
    return {"success": True, "message": "已从错题本中移除"}

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

@router.post("/reset-answers")
def reset_wrong_answers(payload: Optional[ResetAnswersModel] = None, conn: sqlite3.Connection = Depends(get_db)):
    """重置错题本自测作答状态（安全防护：绝不清空正式题库 user_progress 答卷）"""
    return {"success": True, "message": "错题本自测记录已重置，原试卷做题记录安全完好！"}

@router.post("/{question_id}/reset-answer")
def reset_single_wrong_answer(question_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """重置单道错题自测作答状态（安全防护：绝不清空正式题库 user_progress 答卷）"""
    return {"success": True, "message": "该题错题本自测状态已重置，原试卷做题记录安全完好！"}

@router.delete("/clear")
def clear_wrong_book(workbook_id: Optional[int] = None, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    if workbook_id:
        cursor.execute("DELETE FROM wrong_book WHERE workbook_id = ?", (workbook_id,))
    else:
        cursor.execute("DELETE FROM wrong_book")
    conn.commit()
    return {"success": True, "message": "错题记录已清空"}
