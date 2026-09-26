import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

from test_ch2_refined import parse_questions_refined
from test_ch2_stitch import get_clean_chapter_lines
from test_m1_exps import parse_module_explanations

# 1. 获取马原的所有解析
m1_exps = parse_module_explanations('backend/1000_exp_txt', 3, 66)
print(f"Total Explanations in M1: {len(m1_exps)}")

# 2. 获取马原的所有试题
m1_lines = get_clean_chapter_lines('backend/1000_q_txt', 4, 60)
m1_qs = parse_questions_refined(m1_lines)
print(f"Total Questions in M1: {len(m1_qs)}")

# 3. 匹配算法：
# 优先根据局部窗口（如 +/- 3 题）内的关键词重合度进行最优对齐
def extract_keywords(text):
    # 提取4字以上的汉字短语或词语
    words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
    return set(words)

matched = []
unmatched_exps = []
used_q_indices = set()

# 双指针 / 局部窗口动态规划匹配
q_ptr = 0
for exp_idx, exp in enumerate(m1_exps):
    exp_words = extract_keywords(exp['explanation'])
    
    best_q = None
    best_score = 0
    best_q_idx = -1
    
    # 在 q_ptr 附近的窗口搜索
    search_range = range(max(0, q_ptr - 2), min(len(m1_qs), q_ptr + 8))
    for qi in search_range:
        if qi in used_q_indices: continue
        q = m1_qs[qi]
        q_words = extract_keywords(q['stem'])
        overlap = len(exp_words.intersection(q_words))
        # 题号相符加分
        if exp['qnum'] and q['qnum'] == exp['qnum']:
            overlap += 5
        if overlap > best_score:
            best_score = overlap
            best_q = q
            best_q_idx = qi
            
    if best_q and best_score >= 3:
        matched.append((best_q, exp, best_score))
        used_q_indices.add(best_q_idx)
        q_ptr = best_q_idx + 1
    else:
        # 如果窗口没找到，找未使用的最近的一个合格试题
        fallback_q = None
        for qi in range(q_ptr, min(len(m1_qs), q_ptr + 3)):
            if qi not in used_q_indices and len(m1_qs[qi]['options']) >= 3:
                fallback_q = m1_qs[qi]
                best_q_idx = qi
                break
        if fallback_q:
            matched.append((fallback_q, exp, 1))
            used_q_indices.add(best_q_idx)
            q_ptr = best_q_idx + 1
        else:
            unmatched_exps.append(exp)

print(f"Successfully matched: {len(matched)} / {len(m1_exps)} ({len(matched)/len(m1_exps)*100:.1f}%)")
print("\nSample Matched Questions:")
for q, exp, score in matched[:10]:
    print(f"Q (Stem: {q['stem'][:25]}...) | Ans={exp['answer']:4s} | Opts={[o['key'] for o in q['options']]} | Score={score}")
