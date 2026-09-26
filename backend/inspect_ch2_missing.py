import sys
sys.stdout.reconfigure(encoding='utf-8')

from test_m1_qs import parse_module_questions

qs = parse_module_questions('backend/1000_q_txt', 7, 16)
qnums = [q['qnum'] for q in qs]
print(f"Captured {len(qnums)} questions in Ch2:")
print("Qnums:", qnums)
all_expected = set(range(1, 41))
missing = all_expected - set(qnums)
print("Missing numbers:", sorted(missing))
