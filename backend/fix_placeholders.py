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

# Exact mapping for the 19 placeholder items
PATCHES = {
    124: {'C': '生产关系对生产力具有反作用'},
    152: {'D': '生产资本'},
    170: {'B': '商品生产者自发计算的必然结果'},
    195: {'B': '技术创新带来的超额利润'},
    206: {'C': '国家垄断资本主义阻碍了社会化大生产的发展'},
    208: {'D': '资本主义生产关系局部调整的产物'},
    232: {'D': '社会主义必然取代资本主义的历史必然性'},
    236: {'D': '必须建立无产阶级政党'},
    271: {'B': '时代背景', 'D': '目标任务'},
    278: {'D': '党的建设'},
    287: {'C': '中国特色社会主义理论体系'},
    292: {'D': '民族资本主义'},
    323: {'D': '实行改革开放'},
    366: {'B': '发展要有协调性、均衡性', 'D': '发展要有持久性、连续性'},
    376: {'D': '加强生态文明建设'},
    395: {'A': '坚持公有制为主体、多种所有制经济共同发展'},
    479: {'D': '扩大公民有序政治参与'}
}

# Apply patches
updated = 0
for qid, fill in PATCHES.items():
    c.execute("SELECT options_json FROM questions WHERE id = ?", (qid,))
    row = c.fetchone()
    if row:
        opts = json.loads(row[0])
        for o in opts:
            k = o['key']
            if k in fill:
                o['value'] = fill[k]
        c.execute("UPDATE questions SET options_json = ? WHERE id = ?",
                  (json.dumps(opts, ensure_ascii=False), qid))
        updated += 1

conn.commit()

# Double check if any placeholder remains
c.execute("SELECT count(*) FROM questions WHERE workbook_id=4 AND options_json LIKE '%相关选项内容%'")
remaining = c.fetchone()[0]
conn.close()

print(f"Patched {updated} questions. Remaining placeholders in Workbook 4: {remaining}")
