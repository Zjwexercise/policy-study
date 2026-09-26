import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_clean_lines(folder, p):
    f = os.path.join(folder, f'page_{p:03d}.txt')
    if not os.path.exists(f): return []
    with open(f, 'r', encoding='utf-8-sig') as fp:
        text = fp.read()
    prev = ""
    while prev != text:
        prev = text
        text = re.sub(r'([\u4e00-\u9fa5])[ \t]+([\u4e00-\u9fa5])', r'\1\2', text)
        text = re.sub(r'([\u4e00-\u9fa5])[ \t]+([^\w\s])', r'\1\2', text)
        text = re.sub(r'([^\w\s])[ \t]+([\u4e00-\u9fa5])', r'\1\2', text)
    return [l.strip() for l in text.splitlines() if l.strip()]

def find_chapter_headers(folder, max_page=205):
    chap_re = re.compile(r'^(?:[一二三四五]、)?(导论|第[一二三四五六七八九十\d]+章)\s*([\u4e00-\u9fa5]{2,30})')
    mod_re = re.compile(r'^第[一二三四五]部分\s*([\u4e00-\u9fa5]{2,30})')
    
    headers = []
    current_mod = "未知模块"
    
    for p in range(1, max_page + 1):
        lines = get_clean_lines(folder, p)
        for l in lines[:10]: # 前10行
            m_mod = mod_re.match(l)
            if m_mod:
                current_mod = m_mod.group(1).strip()
            m_chap = chap_re.match(l)
            if m_chap:
                c_title = m_chap.group(1) + " " + m_chap.group(2)
                # 避免重复记录相邻页相同的页眉
                if not headers or headers[-1]['title'] != c_title:
                    headers.append({
                        'page': p,
                        'module': current_mod,
                        'title': c_title
                    })
                break
    return headers

print("=== Q Book Chapters ===")
q_headers = find_chapter_headers('backend/1000_q_txt')
for h in q_headers:
    print(f"P{h['page']:03d} | [{h['module']:15s}] | {h['title']}")

print("\n=== Exp Book Chapters ===")
exp_headers = find_chapter_headers('backend/1000_exp_txt')
for h in exp_headers:
    print(f"P{h['page']:03d} | [{h['module']:15s}] | {h['title']}")
