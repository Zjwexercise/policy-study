import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

with open('frontend/public/data/all_questions.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

print(f"Total questions in all_questions.json: {len(qs)}")
cat_counts = {}
for q in qs:
    cat_counts[q['category']] = cat_counts.get(q['category'], 0) + 1

for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"Category {cat}: {count} questions")

# Check 史纲 sample questions
print('\n--- 史纲 Samples (First 5) ---')
shigang_qs = [q for q in qs if q['category'] == '史纲']
for q in shigang_qs[:5]:
    stem_txt = q['stem'][:55]
    exp_txt = q['explanation'][:55]
    print(f"Q{q['id']} [WB{q['workbook_id']}]: {stem_txt} | Ans: {q['answer']} | Exp: {exp_txt}")

# Check 思修 sample questions
print('\n--- 思修 Samples (First 5) ---')
sixiu_qs = [q for q in qs if q['category'] == '思修']
for q in sixiu_qs[:5]:
    stem_txt = q['stem'][:55]
    exp_txt = q['explanation'][:55]
    print(f"Q{q['id']} [WB{q['workbook_id']}]: {stem_txt} | Ans: {q['answer']} | Exp: {exp_txt}")

# Check 习思想 sample questions
print('\n--- 习思想 Samples (First 5) ---')
xi_qs = [q for q in qs if q['category'] == '习思想']
for q in xi_qs[:5]:
    stem_txt = q['stem'][:55]
    exp_txt = q['explanation'][:55]
    print(f"Q{q['id']} [WB{q['workbook_id']}]: {stem_txt} | Ans: {q['answer']} | Exp: {exp_txt}")
