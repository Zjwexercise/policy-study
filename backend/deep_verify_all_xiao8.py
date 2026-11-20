import sqlite3
import json

conn = sqlite3.connect("backend/policy_study.db")
c = conn.cursor()

# Check all stems in WB 41..48
c.execute("SELECT workbook_id, question_num, stem, options_json, answer, explanation FROM questions WHERE workbook_id >= 41 AND workbook_id <= 48 ORDER BY workbook_id, question_num")
rows = c.fetchall()

print(f"Total rows: {len(rows)}")
for wb_id, q_num, stem, opt_json, ans, exp in rows:
    opts = json.loads(opt_json)
    # Check 1: Stem length
    if len(stem.strip()) < 20 and (wb_id, q_num) != (47, 3):
        print(f"[WARN STEM] WB {wb_id} Q{q_num:02d} ({len(stem)} chars): {stem}")
    # Check 2: Option count and empty options
    if len(opts) != 4:
        print(f"[WARN OPT COUNT] WB {wb_id} Q{q_num:02d}: {len(opts)} options")
    for opt in opts:
        if not opt["value"].strip():
            print(f"[WARN EMPTY OPT] WB {wb_id} Q{q_num:02d} Opt {opt['key']}")
    # Check 3: Answer valid
    if not ans:
        print(f"[WARN NO ANS] WB {wb_id} Q{q_num:02d}")
    # Check 4: Explanation valid
    if not exp or len(exp.strip()) < 10:
        print(f"[WARN NO EXP] WB {wb_id} Q{q_num:02d}")

print("Verification pass finished.")
