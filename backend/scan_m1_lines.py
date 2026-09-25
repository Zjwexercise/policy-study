import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

with open('backend/m1_raw_ocr.txt', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
found_nums = []
for idx, l in enumerate(lines):
    m = re.match(r'^\s*(\d{1,2})\s*([·\.、．，,\s])\s*(.*)', l)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 30:
            found_nums.append((num, idx, l))

print(f"Found {len(found_nums)} candidate question lines:")
for num, idx, l in found_nums:
    print(f"  Line {idx+1:3d} | Q{num:2d}: {l[:60]}")
