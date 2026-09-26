import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 检查第2章的试题和解析
# Q pages: 7 .. 16
# Exp pages: 6 .. 17

def inspect_chapter_numbers(folder, start_p, end_p, is_exp=False):
    numbers = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            lines = fp.readlines()
        for l in lines:
            l_str = re.sub(r'\s+', '', l)
            if not is_exp:
                m = re.match(r'^(\d{1,3})[\.、．·:：]', l_str)
                if m:
                    numbers.append((p, int(m.group(1)), l.strip()[:40]))
            else:
                m = re.search(r'(?:^|[\s\n])(?:(\d{1,3})[\.、．·:：\s]*)?(?:答案|爷案|答索|案|〕)?\s*([A-D]{1,4})\s*[〖（\[(【]解析', l_str)
                if m:
                    q_num = m.group(1)
                    ans = m.group(2)
                    numbers.append((p, q_num, ans, l.strip()[:40]))
    return numbers

print("=== Q numbers in Ch2 ===")
q_nums = inspect_chapter_numbers('backend/1000_q_txt', 7, 16, is_exp=False)
for p, num, text in q_nums[:20]:
    print(f"P{p:03d} Q{num:2d}: {text}")
print(f"Total Q found: {len(q_nums)}, Max num: {max(n[1] for n in q_nums)}")

print("\n=== Exp answers in Ch2 ===")
exp_nums = inspect_chapter_numbers('backend/1000_exp_txt', 6, 17, is_exp=True)
for p, num, ans, text in exp_nums[:20]:
    print(f"P{p:03d} Q{str(num):4s} Ans={ans:4s}: {text}")
print(f"Total Exp found: {len(exp_nums)}")
