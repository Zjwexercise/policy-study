import sys
import io
import json
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('frontend/public/data/all_questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

print(f"Total questions in database: {len(questions)}")

broken = []
for q in questions:
    stem = q.get('stem', '').strip()
    ans = q.get('answer', '').strip()
    opts = q.get('options', [])
    opt_keys = [o['key'] for o in opts]
    
    reasons = []
    # 1. Answer has letter not in options
    for a in ans:
        if a not in opt_keys:
            reasons.append(f"Answer {ans} has letter {a} not in options {opt_keys}")
            break
            
    # 2. Options < 4
    if len(opts) < 4:
        reasons.append(f"Only {len(opts)} options")
        
    # 3. Stem too short or broken prompt
    if len(stem) < 8 or stem.startswith('阅读材料') or stem.startswith('材料 1') or stem.startswith('材料 2'):
        reasons.append(f"Broken stem: '{stem[:30]}'")
        
    if reasons:
        broken.append((q['id'], q['workbook_id'], q['question_num'], reasons))

print(f"Total broken/unsolvable questions: {len(broken)}")
print("Broken count by workbook:", Counter([b[1] for b in broken]))
for b in broken[:15]:
    print(f"  ID {b[0]} (WB {b[1]} Q{b[2]}): {b[3]}")
