import sqlite3
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('backend/policy_study.db')
c = conn.cursor()

print("=" * 60)
print("1. VERIFY WORKBOOK 6 - 史纲 Q3 and Q4 (User screenshot issue)")
print("=" * 60)
c.execute("""
    SELECT question_num, stem, options_json, answer 
    FROM questions 
    WHERE workbook_id = 6 AND (stem LIKE '%维新派%' OR options_json LIKE '%均贫富%')
""")
rows = c.fetchall()
for r in rows:
    print(f"Qnum: {r[0]}")
    print(f"Stem: {r[1]}")
    opts = json.loads(r[2])
    for o in opts:
        print(f"  {o['key']}. {o['value']}")
    print(f"Ans: {r[3]}")
    print("-" * 50)

print("\n" + "=" * 60)
print("2. VERIFY WORKBOOK 1 - 精选真题集 (Contamination check)")
print("=" * 60)
c.execute("""
    SELECT count(*) FROM questions 
    WHERE workbook_id = 4 AND (options_json LIKE '%出发点永远%' OR options_json LIKE '%断纯背%' OR options_json LIKE '%本质%')
""")
print(f"Teacher commentary options in WB 4: {c.fetchone()[0]}")

print("\n" + "=" * 60)
print("3. WORKBOOK SUMMARY ACROSS ALL 3 BOOKS")
print("=" * 60)
c.execute("SELECT id, name, total_questions FROM workbooks ORDER BY id")
for wb in c.fetchall():
    print(f"Workbook {wb[0]}: {wb[1]} -> Total questions: {wb[2]}")
    
    # 类别统计
    c.execute("SELECT category, count(*) FROM questions WHERE workbook_id = ? GROUP BY category", (wb[0],))
    cats = c.fetchall()
    print("  Category breakdown:", dict(cats))
    
    # 答案有效性
    c.execute("SELECT count(*) FROM questions WHERE workbook_id = ? AND answer NOT GLOB '[A-D]*'", (wb[0],))
    invalid_ans = c.fetchone()[0]
    print(f"  Invalid answers: {invalid_ans}")

conn.close()
