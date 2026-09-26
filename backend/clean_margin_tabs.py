import sqlite3
import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('backend/policy_study.db')
c = conn.cursor()
c.execute('SELECT id, workbook_id, question_num, options_json FROM questions')
dirty_count = 0

for row in c.fetchall():
    qid, wbid, qnum, opts_raw = row
    opts = json.loads(opts_raw)
    changed = False
    new_opts = []
    for o in opts:
        val = o['value']
        orig = val
        
        # 1. 移除诸如 "、 多项选择题", "多项选择题", "单项选择题"
        val = re.sub(r'[\s、,，\ufeff]*[单多]?项选择题[\s\S]*$', '', val).strip()
        # 2. 移除诸如 "第 四 部", "第四部分", "第 一 部 分"
        val = re.sub(r'[\s、,，\ufeff]*第\s*[一二三四五]\s*部\s*分?[\s\S]*$', '', val).strip()
        # 3. 移除末尾的章名干扰，如 "第二章实践与认识及其发展规律纲基、"
        val = re.sub(r'[\s、,，\ufeff]*第[一二三四五六七八九十\d]+章[\u4e00-\u9fa5]+[\s\S]*$', '', val).strip()
        # 4. 移除末尾残留的 "\ufeff” 马克思主义基庫原瓔"
        val = re.sub(r'[\s、,，\ufeff]*[“\"]?\s*马克思主义[\u4e00-\u9fa5]+[\s\S]*$', '', val).strip()
        # 5. 移除末尾残留的标点符号如 "、", "，", ","
        val = re.sub(r'[\s、,，\ufeff]+$', '', val).strip()
        
        if val != orig:
            changed = True
            dirty_count += 1
            print(f"Refined WB{wbid} Q{qnum} Opt {o['key']}: {repr(orig)} -> {repr(val)}")
            o['value'] = val
        new_opts.append(o)
    if changed:
        c.execute('UPDATE questions SET options_json = ? WHERE id = ?', (json.dumps(new_opts, ensure_ascii=False), qid))

conn.commit()
print(f"Total options refined across database: {dirty_count}")
conn.close()
