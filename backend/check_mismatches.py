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

c.execute('SELECT id, question_num, stem, options_json, answer, explanation FROM questions WHERE workbook_id = 6')
rows = c.fetchall()

print(f"《徐涛优题库》共 {len(rows)} 题，正在全面比对选项与解析一致性...")
flagged = []
for qid, num, stem, opts_json, ans, exp in rows:
    opts = json.loads(opts_json)
    opts_dict = {o['key']: o['value'] for o in opts}
    
    # 查找解析中明确指出的正确选项关键词
    # 例如：只有选项A提到了“人民” / 选项A“主观唯心主义”
    m_exp_kw = re.search(r'选项([A-D])(?:正确|提到了[“\"]([^”\"]+)[”\"])', exp)
    if m_exp_kw:
        target_opt = m_exp_kw.group(1)
        kw = m_exp_kw.group(2)
        if kw and target_opt in opts_dict:
            if kw not in opts_dict[target_opt]:
                flagged.append((qid, num, stem[:40], target_opt, kw, opts_dict[target_opt], exp[:60]))

print(f"发现明显选项与解析关键词不符的题目: {len(flagged)} 处：")
for f in flagged:
    print(f"ID {f[0]} Q{f[1]}:")
    print(f"  题干: {f[2]}")
    print(f"  解析要求选项{f[3]}包含关键词: 【{f[4]}】")
    print(f"  但当前选项{f[3]}内容为: 【{f[5]}】")
    print(f"  解析摘要: {f[6]}")
    print("-" * 50)

conn.close()
