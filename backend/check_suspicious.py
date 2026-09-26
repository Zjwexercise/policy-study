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

normal = [r for r in rows if '【考研政治刷题计划名师解析】' not in (r[6] or '')]
suspicious = []
for r in normal:
    stem = r[3]
    opts = json.loads(r[4])
    expl = r[6] or ''
    words = [w for w in re.findall(r'[\u4e00-\u9fa5]{2,6}', stem) if len(w)>=2 and w not in ['可以','能够','因为','这是','为了','说明','进行','关于','以及','我们','必须']]
    opt_str = ' '.join([o.get('value','') for o in opts])
    has_opt = any(w in opt_str for w in words)
    has_exp = any(w in expl for w in words)
    if not has_opt and not has_exp:
        suspicious.append(r)

print(f"Total suspicious: {len(suspicious)}")
for r in suspicious[:10]:
    opts = json.loads(r[4])
    opt_str = ' | '.join([f"{o['key']}:{o['value'][:15]}" for o in opts])
    print(f"ID {r[0]} | Q{r[1]} [{r[2]}] Ans:{r[5]}")
    print(f"  Stem: {r[3][:70]}")
    print(f"  Opts: {opt_str}")
    print(f"  Expl: {r[6][:70] if r[6] else ''}")
    print('-'*50)
