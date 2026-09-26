import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 检查 M1 的每个章节的题目和解析数量
# M1 章节起始页 (Q 和 Exp):
chapters = [
    ("导论", 4, 6, 3, 6),
    ("第二章 世界的物质性及发展规律", 7, 16, 6, 17),
    ("第三章 实践与认识及其发展规律", 17, 26, 17, 27),
    ("第四章 人类社会及其发展规律", 27, 36, 27, 38),
    ("第五章 资本主义的本质及规律", 37, 47, 39, 50),
    ("第六章 资本主义的发展及其趋势", 48, 53, 51, 58),
    ("第七章 社会主义的发展及其规律", 54, 57, 59, 62),
    ("第八章 共产主义崇高理想及其最终实现", 58, 60, 63, 66),
]

from test_m1_qs import parse_module_questions
from test_m1_exps import parse_module_explanations

for name, q_s, q_e, exp_s, exp_e in chapters:
    qs = parse_module_questions('backend/1000_q_txt', q_s, q_e)
    exps = parse_module_explanations('backend/1000_exp_txt', exp_s, exp_e)
    print(f"{name:32s} | Q: {len(qs):2d} | Exp: {len(exps):2d}")
