import os
import json
import sqlite3
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional, List
from database import get_db, UPLOAD_DIR
from pdf_parser import parse_politics_pdf

router = APIRouter(prefix="/api/workbooks", tags=["workbooks"])

@router.get("")
def list_workbooks(conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        w.id, w.name, w.filename, w.total_questions, w.description, w.created_at,
        COUNT(DISTINCT up.question_id) as answered_count,
        SUM(CASE WHEN up.is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
        COUNT(DISTINCT wb.question_id) as wrong_count
    FROM workbooks w
    LEFT JOIN user_progress up ON w.id = up.workbook_id
    LEFT JOIN wrong_book wb ON w.id = wb.workbook_id AND wb.is_mastered = 0
    GROUP BY w.id
    ORDER BY w.id DESC
    """)
    rows = cursor.fetchall()
    
    result = []
    for r in rows:
        total = r["total_questions"] or 0
        answered = r["answered_count"] or 0
        correct = r["correct_count"] or 0
        wrong = r["wrong_count"] or 0
        accuracy = round((correct / answered * 100), 1) if answered > 0 else 0
        
        result.append({
            "id": r["id"],
            "name": r["name"],
            "filename": r["filename"],
            "total_questions": total,
            "answered_count": answered,
            "correct_count": correct,
            "wrong_count": wrong,
            "accuracy": accuracy,
            "description": r["description"],
            "created_at": r["created_at"]
        })
    return result

@router.get("/{workbook_id}")
def get_workbook(workbook_id: int, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workbooks WHERE id = ?", (workbook_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="练习册不存在")
    
    # 统计分类与题型分布
    cursor.execute("""
        SELECT category, question_type, COUNT(*) as count 
        FROM questions 
        WHERE workbook_id = ? 
        GROUP BY category, question_type
    """, (workbook_id,))
    cats = cursor.fetchall()

    return {
        "id": row["id"],
        "name": row["name"],
        "filename": row["filename"],
        "total_questions": row["total_questions"],
        "description": row["description"],
        "created_at": row["created_at"],
        "breakdown": [dict(c) for c in cats]
    }

@router.post("/upload")
def upload_pdf(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    conn: sqlite3.Connection = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="请上传 PDF 格式文件")

    wb_name = name or os.path.splitext(file.filename)[0]
    safe_filename = f"{int(os.path.getmtime(UPLOAD_DIR) if os.path.exists(UPLOAD_DIR) else 0)}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 调用 PDF 智能解析引擎
    try:
        parse_result = parse_politics_pdf(save_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF解析失败: {str(e)}")

    questions = parse_result.get("questions", [])
    if not questions:
        raise HTTPException(
            status_code=422, 
            detail="未能从该PDF中识别出题目。请检查该PDF是否为可编辑文本（扫描件需先OCR），或排版格式是否规范。"
        )

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO workbooks (name, filename, file_path, total_questions, description)
    VALUES (?, ?, ?, ?, ?)
    """, (
        wb_name,
        file.filename,
        save_path,
        len(questions),
        f"由文件 {file.filename} 解析导入，共识别 {len(questions)} 道题目"
    ))
    workbook_id = cursor.lastrowid

    for idx, q in enumerate(questions):
        cursor.execute("""
        INSERT INTO questions (workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workbook_id,
            q.get("question_num", idx + 1),
            q.get("question_type", "single"),
            q.get("category", "综合"),
            q.get("stem", ""),
            json.dumps(q.get("options", []), ensure_ascii=False),
            q.get("answer", ""),
            q.get("explanation", ""),
            idx + 1
        ))

    conn.commit()

    return {
        "success": True,
        "workbook_id": workbook_id,
        "name": wb_name,
        "total_parsed": len(questions),
        "message": f"成功解析并导入 {len(questions)} 道考研政治题目！"
    }

@router.post("/{workbook_id}/reset")
def reset_workbook_progress(workbook_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """重置练习进度（用于二刷、三刷，重置已答题目和错题记录）"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM workbooks WHERE id = ?", (workbook_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="练习册不存在")

    cursor.execute("DELETE FROM user_progress WHERE workbook_id = ?", (workbook_id,))
    cursor.execute("DELETE FROM wrong_book WHERE workbook_id = ?", (workbook_id,))
    conn.commit()

    return {"success": True, "message": "练习进度已重置，可以开始全新一轮刷题！"}

@router.delete("/{workbook_id}")
def delete_workbook(workbook_id: int, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM workbooks WHERE id = ?", (workbook_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="练习册不存在")
    
    file_path = row["file_path"]
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    cursor.execute("DELETE FROM workbooks WHERE id = ?", (workbook_id,))
    cursor.execute("DELETE FROM questions WHERE workbook_id = ?", (workbook_id,))
    cursor.execute("DELETE FROM user_progress WHERE workbook_id = ?", (workbook_id,))
    cursor.execute("DELETE FROM wrong_book WHERE workbook_id = ?", (workbook_id,))
    conn.commit()

    return {"success": True, "message": "练习册已删除"}
