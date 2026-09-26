import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('backend/1000_exp_txt/page_003.txt', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

for i, l in enumerate(lines[:35]):
    if '解' in l:
        print(f"L{i+1}: {repr(l.strip())}")
