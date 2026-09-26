import sqlite3
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

conn = sqlite3.connect('backend/policy_study.db')
c = conn.cursor()
target_ids = [56, 174, 208, 217, 222, 231, 232, 396, 408]
c.execute(f"SELECT id, question_num, stem, options_json, answer, explanation FROM questions WHERE id IN ({','.join(map(str, target_ids))})")
for r in c.fetchall():
    print(f"=== ID {r[0]} (Q{r[1]}) ===")
    print("Stem:", r[2])
    opts = json.loads(r[3])
    for opt in opts:
        print(f"  {opt['key']}: {opt['value']}")
    print("Ans:", r[4])
    print("Exp:", r[5])
    print()
