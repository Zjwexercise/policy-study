import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

from test_ch2_refined import parse_questions_refined
from test_ch2_stitch import get_clean_chapter_lines

q_modules = [
    ("马原", 4, 60),
    ("毛中特", 61, 82),
    ("习思想", 83, 127),
    ("史纲", 128, 178),
    ("思修", 179, 205),
]

for mod_name, s, e in q_modules:
    lines = get_clean_chapter_lines('backend/1000_q_txt', s, e)
    qs = parse_questions_refined(lines)
    full_opts = sum(1 for q in qs if len(q['options']) == 4)
    print(f"[{mod_name:6s}] Q Pages {s:3d}..{e:3d} | Parsed Q: {len(qs):3d} | 4-Option Q: {full_opts:3d} ({full_opts/len(qs)*100:.1f}%)")
