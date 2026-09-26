import sqlite3
import json
import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

conn = sqlite3.connect('backend/policy_study.db')
c = conn.cursor()
c.execute("SELECT id, question_num, stem, options_json, answer, explanation FROM questions WHERE workbook_id=4 AND options_json LIKE '%相关选项内容%'")
rows = c.fetchall()

print(f"Total placeholders: {len(rows)}")
for r in rows:
    opts = json.loads(r[3])
    missing_keys = [o['key'] for o in opts if '相关选项内容' in o['value']]
    print(f"ID {r[0]} | Q{r[1]} | Ans: {r[4]} | Missing: {missing_keys}")
    print(f"  Stem: {r[2][:70]}")
    print(f"  Expl: {r[5][:80] if r[5] else ''}")
    print('-'*50)
