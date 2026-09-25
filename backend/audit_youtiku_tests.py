import sqlite3
import re

conn = sqlite3.connect('backend/policy_study.db')
c = conn.cursor()

c.execute('SELECT id, question_num, stem FROM questions WHERE workbook_id = 6 ORDER BY id ASC')
rows = c.fetchall()

tests = {}
for qid, num, stem in rows:
    m = re.match(r'【(综合测试[一二三四五六七八九十\d]+)】', stem)
    tname = m.group(1) if m else "未知"
    if tname not in tests:
        tests[tname] = []
    tests[tname].append((num, qid))

for tname, qlist in tests.items():
    nums = [x[0] for x in qlist]
    print(f"{tname}: 共 {len(nums)} 题, 题号范围 {min(nums)}~{max(nums)}")
    # 查找是否有重复题号或缺失
    missing = [i for i in range(1, max(nums)+1) if i not in nums]
    if missing:
        print(f"   缺失题号: {missing}")

conn.close()
