import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

from test_m1_exps import parse_module_explanations

modules = [
    ("马原", 3, 66),
    ("毛中特", 67, 88),
    ("习思想", 89, 129),
    ("史纲", 130, 182),
    ("思修", 183, 204),
]

all_exps = {}
for mod_name, s, e in modules:
    items = parse_module_explanations('backend/1000_exp_txt', s, e)
    valid_ans = sum(1 for x in items if re.match(r'^[A-D]+$', x['answer']))
    print(f"[{mod_name:6s}] Pages {s:3d}..{e:3d} | Total Exp: {len(items):3d} | Valid Ans: {valid_ans:3d} ({valid_ans/len(items)*100:.1f}%)")
    all_exps[mod_name] = items

total = sum(len(v) for v in all_exps.values())
print(f"\nGRAND TOTAL EXPLANATIONS IN 1000题: {total}")
