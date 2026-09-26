import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def find_all_chapters(folder):
    files = sorted(glob.glob(os.path.join(folder, '*.txt')))
    records = []
    
    # 标准章节名正则表达式
    # 导论 / 第一章 ... / 第二章 ...
    chap_re = re.compile(r'(导论|第[一二三四五六七八九十\d]+章)\s*([^\n\r]{0,30})')
    mod_re = re.compile(r'第[一二三四五]部分\s*([^\n\r]{0,30})')
    
    for f in files:
        pnum = int(os.path.basename(f).split('_')[1].split('.')[0])
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = fp.read()
        
        # 消除空格
        clean_text = ""
        prev = ""
        t = text
        while prev != t:
            prev = t
            t = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', t)
        
        lines = [l.strip() for l in t.splitlines() if l.strip()]
        for l in lines[:10]: # 章节名通常在前10行
            m_mod = mod_re.search(l)
            if m_mod:
                records.append((pnum, "MODULE", m_mod.group(0)))
            m_chap = chap_re.search(l)
            if m_chap:
                # 排除正文中引用，例如“在第一章中”
                if any(x in l for x in ['在', '从', '由', '见', '和', '与', '的', '及', '考查', '题', '选项']) and not any(l.startswith(x) for x in ['第', '导论', '一、', '二、', '【']):
                    continue
                records.append((pnum, "CHAP", m_chap.group(0)))
    return records

print("=== Q Folders Chapters ===")
q_chaps = find_all_chapters('backend/1000_q_txt')
for r in q_chaps:
    print(f"P{r[0]:03d} [{r[1]:6s}] {r[2]}")

print("\n=== Exp Folders Chapters ===")
exp_chaps = find_all_chapters('backend/1000_exp_txt')
for r in exp_chaps:
    print(f"P{r[0]:03d} [{r[1]:6s}] {r[2]}")
