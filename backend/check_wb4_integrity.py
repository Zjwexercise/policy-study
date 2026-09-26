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

print(f"Total questions in Workbook 4: {len(rows)}")

# Let's inspect any anomalies:
# 1. Option count != 4
abnormal_opts = []
for r in rows:
    opts = json.loads(r[4])
    if len(opts) != 4:
        abnormal_opts.append((r[0], r[1], len(opts), [o['key'] for o in opts]))

print(f"Questions with != 4 options: {len(abnormal_opts)}")
for a in abnormal_opts[:10]:
    print(f"  ID {a[0]} Q{a[1]}: {a[2]} opts -> {a[3]}")

# 2. Options with duplicate keys or empty values
bad_opt_values = []
for r in rows:
    opts = json.loads(r[4])
    for o in opts:
        if not o.get('value') or len(o['value'].strip()) < 1:
            bad_opt_values.append((r[0], r[1], o['key']))

print(f"Questions with empty option values: {len(bad_opt_values)}")

# 3. Answer not in options
bad_answers = []
for r in rows:
    opts = json.loads(r[4])
    keys = {o['key'] for o in opts}
    ans = r[5]
    for char in ans:
        if char not in keys:
            bad_answers.append((r[0], r[1], ans, keys))
            break

print(f"Questions with invalid answer keys: {len(bad_answers)}")
for b in bad_answers[:10]:
    print(f"  ID {b[0]} Q{b[1]}: ans={b[2]}, opt_keys={b[3]}")
