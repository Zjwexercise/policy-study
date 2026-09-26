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
c.execute('SELECT id, question_num, stem, options_json, answer, explanation FROM questions WHERE workbook_id=4 ORDER BY id LIMIT 30')
rows = c.fetchall()

print(f"Total inspected: {len(rows)}")
for r in rows:
    opts = json.loads(r[3])
    opt_summary = ' | '.join([f"{o.get('key')}: {o.get('value','')[:15]}" for o in opts])
    print(f"ID {r[0]} | Q{r[1]} | Ans: {r[4]}")
    print(f"  Stem: {r[2][:70]}")
    print(f"  Opts: {opt_summary}")
    print(f"  Expl: {r[5][:70] if r[5] else ''}")
    print('-'*50)
