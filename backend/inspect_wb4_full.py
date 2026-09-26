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
c.execute('SELECT id, question_num, category, stem, options_json, answer, explanation FROM questions WHERE workbook_id=4 ORDER BY id')
rows = c.fetchall()

print(f"Total in WB4: {len(rows)}")

# Let's inspect samples across the entire workbook
sample_indices = [0, 5, 10, 15, 20, 30, 50, 100, 200, 300, 400, 450]
for idx in sample_indices:
    if idx < len(rows):
        r = rows[idx]
        opts = json.loads(r[4])
        opt_s = " | ".join([f"{o['key']}:{o['value'][:15]}" for o in opts])
        print(f"--- Index {idx} (ID {r[0]} | Q{r[1]} | {r[2]} | Ans: {r[5]}) ---")
        print(f"Stem: {r[3][:80]}")
        print(f"Opts: {opt_s}")
        print(f"Expl: {r[6][:80] if r[6] else ''}\n")
