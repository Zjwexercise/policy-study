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
c.execute('SELECT id, question_num, stem, options_json, answer, explanation FROM questions WHERE workbook_id=6 AND stem LIKE "%综合测试一%" AND category="马原" ORDER BY id')
rows = c.fetchall()

print(f'Total questions in 马原·综合测试一: {len(rows)}')
for r in rows:
    opts = json.loads(r[3])
    opt_summary = ' | '.join([f"{o['key']}: {o['value'][:12]}" for o in opts])
    print(f'ID {r[0]} | Q{r[1]} | Ans: {r[4]}')
    print(f'  Stem: {r[2][:60]}')
    print(f'  Opts: {opt_summary}')
    print(f'  Expl: {r[5][:60]}')
