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
c.execute('SELECT id, question_num, category, stem, options_json, answer, explanation FROM questions WHERE workbook_id=4 ORDER BY id')
rows = c.fetchall()

bad_answers = []
for r in rows:
    opts = json.loads(r[4])
    keys = {o['key'] for o in opts}
    ans = r[5]
    for char in ans:
        if char not in keys:
            bad_answers.append(r)
            break

print(f"Total with missing answer letter: {len(bad_answers)}")
for r in bad_answers[:10]:
    opts = json.loads(r[4])
    opt_keys = [o['key'] for o in opts]
    print(f"ID {r[0]} | Q{r[1]} [{r[2]}] | Ans: {r[5]} | Keys: {opt_keys}")
    print(f"  Stem: {r[3][:60]}")
    print(f"  Expl: {r[6][:60] if r[6] else ''}")
    print('-'*50)
