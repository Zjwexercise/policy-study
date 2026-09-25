import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "policy_study.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "frontend", "public", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. 导出 workbooks
cursor.execute("SELECT id, name, filename, total_questions, description FROM workbooks ORDER BY id")
workbooks = []
for row in cursor.fetchall():
    workbooks.append({
        "id": row[0],
        "name": row[1],
        "filename": row[2],
        "total_questions": row[3],
        "description": row[4]
    })

with open(os.path.join(OUTPUT_DIR, "workbooks.json"), "w", encoding="utf-8") as f:
    json.dump(workbooks, f, ensure_ascii=False, indent=2)

print(f"Exported {len(workbooks)} workbooks to workbooks.json")

# 2. 导出每个 workbook 的题目
for wb in workbooks:
    wb_id = wb["id"]
    cursor.execute("""
    SELECT id, workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num
    FROM questions WHERE workbook_id = ? ORDER BY order_num ASC, question_num ASC, id ASC
    """, (wb_id,))
    
    questions = []
    for r in cursor.fetchall():
        questions.append({
            "id": r[0],
            "workbook_id": r[1],
            "question_num": r[2],
            "question_type": r[3],
            "category": r[4] or "综合",
            "stem": r[5],
            "options": json.loads(r[6]),
            "answer": r[7],
            "explanation": r[8] or "",
            "order_num": r[9]
        })
        
    wb_file = os.path.join(OUTPUT_DIR, f"questions_{wb_id}.json")
    with open(wb_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False)
        
    file_size_kb = round(os.path.getsize(wb_file) / 1024, 1)
    print(f"Workbook {wb_id} ({wb['name']}): Exported {len(questions)} questions ({file_size_kb} KB)")

# 3. 导出全量题目 all_questions.json
cursor.execute("""
SELECT id, workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num
FROM questions ORDER BY workbook_id ASC, order_num ASC, question_num ASC, id ASC
""")
all_questions = []
for r in cursor.fetchall():
    all_questions.append({
        "id": r[0],
        "workbook_id": r[1],
        "question_num": r[2],
        "question_type": r[3],
        "category": r[4] or "综合",
        "stem": r[5],
        "options": json.loads(r[6]),
        "answer": r[7],
        "explanation": r[8] or "",
        "order_num": r[9]
    })

all_file = os.path.join(OUTPUT_DIR, "all_questions.json")
with open(all_file, "w", encoding="utf-8") as f:
    json.dump(all_questions, f, ensure_ascii=False)

print(f"All questions: Exported {len(all_questions)} questions to all_questions.json ({round(os.path.getsize(all_file)/1024, 1)} KB)")

conn.close()
