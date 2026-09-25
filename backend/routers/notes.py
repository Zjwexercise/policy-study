import json
import sqlite3
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/api/notes", tags=["notes"])

class NoteModel(BaseModel):
    content: str

@router.get("")
def list_notes(workbook_id: Optional[int] = None, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    query = """
    SELECT 
        n.id as note_id, n.question_id, n.content, n.updated_at,
        q.question_num, q.question_type, q.category, q.stem, q.options_json, q.answer, q.explanation,
        w.id as workbook_id, w.name as workbook_name
    FROM notes n
    JOIN questions q ON n.question_id = q.id
    JOIN workbooks w ON q.workbook_id = w.id
    WHERE 1=1
    """
    params = []
    if workbook_id:
        query += " AND w.id = ?"
        params.append(workbook_id)

    query += " ORDER BY n.updated_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        try:
            options = json.loads(r["options_json"])
        except Exception:
            options = []

        results.append({
            "note_id": r["note_id"],
            "question_id": r["question_id"],
            "content": r["content"],
            "updated_at": r["updated_at"],
            "workbook_id": r["workbook_id"],
            "workbook_name": r["workbook_name"],
            "question_num": r["question_num"],
            "question_type": r["question_type"],
            "category": r["category"],
            "stem": r["stem"],
            "options": options,
            "answer": r["answer"],
            "explanation": r["explanation"]
        })
    return results

@router.post("/{question_id}")
def save_note(question_id: int, payload: NoteModel, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="题目不存在")

    content = payload.content.strip()
    if not content:
        # 如果内容为空，删除笔记
        cursor.execute("DELETE FROM notes WHERE question_id = ?", (question_id,))
    else:
        cursor.execute("""
        INSERT INTO notes (question_id, content, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(question_id) DO UPDATE SET
            content = excluded.content,
            updated_at = CURRENT_TIMESTAMP
        """, (question_id, content))
    conn.commit()

    return {"success": True, "message": "笔记已保存"}

@router.delete("/{question_id}")
def delete_note(question_id: int, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE question_id = ?", (question_id,))
    conn.commit()
    return {"success": True, "message": "笔记已删除"}
