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
c.execute('SELECT id, workbook_id, question_num, stem, options_json, answer, explanation FROM questions')
rows = c.fetchall()

suspicious = []
for qid, wbid, num, stem, opts_json, ans, exp in rows:
    opts = json.loads(opts_json)
    # 1. 检查选项里是否混入了下一题题号
    for o in opts:
        val = o['value']
        if re.search(r'\d{1,3}\s*[·\.、．，,]\s*[\u4e00-\u9fa5“\"\'《]', val):
            suspicious.append((qid, wbid, num, "选项混入下一题题号", o['key'], val[:50]))
    # 2. 检查题干中间是否出现了新的题号
    m_stem = re.search(r'[\u4e00-\u9fa5。？！；\n]\s*(\d{1,3})\s*[·\.、．，,]\s*([\u4e00-\u9fa5“\"\'《])', stem[15:])
    if m_stem:
        suspicious.append((qid, wbid, num, "题干混入下一题", m_stem.group(1), stem[:60]))

print(f"全库共扫描 {len(rows)} 道题，发现疑似两题粘连/选项错位的题目共 {len(suspicious)} 处：")
for s in suspicious:
    print(s)

conn.close()
