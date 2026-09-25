import sqlite3
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from parse_m1_clean import questions_data

conn = sqlite3.connect('backend/policy_study.db')
cursor = conn.cursor()

# 1. 查找旧的 马原·综合测试一 的 ID 范围
cursor.execute('SELECT id FROM questions WHERE workbook_id = 6 AND stem LIKE "%综合测试一%" AND category = "马原" ORDER BY id')
old_ids = [r[0] for r in cursor.fetchall()]
print(f"Old question IDs to replace ({len(old_ids)}): {old_ids}")

# 2. 删除这批旧题
if old_ids:
    cursor.execute(f"DELETE FROM questions WHERE id IN ({','.join(map(str, old_ids))})")
    cursor.execute(f"DELETE FROM wrong_book WHERE question_id IN ({','.join(map(str, old_ids))})")
    cursor.execute(f"DELETE FROM user_progress WHERE question_id IN ({','.join(map(str, old_ids))})")

# 3. 重新插入 30 道精校题目
# 按照 order_num 从 1 到 30 插入
for q in questions_data:
    cursor.execute("""
    INSERT INTO questions (
        workbook_id, question_num, question_type, category,
        stem, options_json, answer, explanation, order_num
    ) VALUES (6, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        q['qnum'],
        q['type'],
        q['category'],
        q['stem'],
        json.dumps(q['options'], ensure_ascii=False),
        q['answer'],
        q['explanation'],
        q['qnum']
    ))

# 4. 更新 workbooks 总题数
cursor.execute("SELECT count(*) FROM questions WHERE workbook_id = 6")
new_total = cursor.fetchone()[0]
cursor.execute("UPDATE workbooks SET total_questions = ? WHERE id = 6", (new_total,))
conn.commit()
conn.close()

print(f"Successfully inserted {len(questions_data)} calibrated questions for 马原·综合测试一!")
print(f"Workbook 6 total questions now: {new_total}")
