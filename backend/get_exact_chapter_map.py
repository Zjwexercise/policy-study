import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 自动从 txt 中按页寻找所有章节的精确起始页
def get_chapter_map(folder):
    files = sorted(glob.glob(os.path.join(folder, '*.txt')))
    chap_starts = []
    
    # 模式
    # 导论 / 第一章 ...
    chap_pat = re.compile(r'(导\s*论|第\s*[一二三四五六七八九十\d]+\s*章)\s*([\u4e00-\u9fa5]{2,25})')
    mod_pat = re.compile(r'第\s*[一二三四五]\s*部\s*分\s*([\u4e00-\u9fa5]{2,25})')
    
    current_chap = None
    for f in files:
        p = int(os.path.basename(f).split('_')[1].split('.')[0])
        with open(f, 'r', encoding='utf-8-sig') as fp:
            lines = [l.strip() for l in fp if l.strip()]
        
        # 只看前 6 行
        for l in lines[:6]:
            l_clean = re.sub(r'\s+', '', l)
            m = chap_pat.search(l_clean)
            if m:
                # 排除正文中引用，例如“在第一章中”
                if any(x in l for x in ['在', '从', '由', '见', '和', '与', '的', '及', '考查', '题', '选项']):
                    continue
                c_name = m.group(1) + " " + m.group(2)
                # 规范化：去除末尾标点
                c_name = re.sub(r'[\.、．·:：•\s]+$', '', c_name)
                if c_name != current_chap:
                    chap_starts.append((p, c_name))
                    current_chap = c_name
                break
    return chap_starts

print("=== Q Book Chapter Starts ===")
q_starts = get_chapter_map('backend/1000_q_txt')
for p, c in q_starts:
    print(f"P{p:03d}: {c}")

print("\n=== Exp Book Chapter Starts ===")
exp_starts = get_chapter_map('backend/1000_exp_txt')
for p, c in exp_starts:
    print(f"P{p:03d}: {c}")
