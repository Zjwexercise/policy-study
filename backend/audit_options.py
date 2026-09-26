import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

with open('frontend/public/data/all_questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

for q in qs:
    for opt in q.get('options', []):
        v = opt.get('value', '')
        # Check suspicious
        if len(v) > 75 or any(k in v for k in ['二维码', '扫码', '公众号', '这是因为', '这表明', '主要是因为', '根本原因是', '谕旨', '总书记指出', '毛泽东指出']):
            wb = q.get('workbook_id')
            qnum = q.get('question_num')
            stem = q.get('stem', '')[:30]
            print(f"Q{q['id']} [WB{wb} Q{qnum}] Opt {opt['key']} (len {len(v)}): {v}")
