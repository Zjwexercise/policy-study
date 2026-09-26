import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def scan_chapters(folder):
    files = sorted(glob.glob(os.path.join(folder, '*.txt')))
    results = []
    current_module = ""
    for f in files:
        pnum = int(os.path.basename(f).split('_')[1].split('.')[0])
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = fp.read()
        # 消除空格
        text_clean = re.sub(r'\s+', '', text)
        
        # 检查模块
        m_mod = re.search(r'(第[一二三四五]部分[\u4e00-\u9fa5]+)', text_clean[:200])
        if m_mod:
            mod_title = m_mod.group(1)
            if mod_title != current_module:
                current_module = mod_title
                results.append((pnum, "MODULE", mod_title))
                
        # 检查章节
        # 章节模式：第[一二三四五六七八九十\d]+章[\u4e00-\u9fa5]+ 或 导论[\u4e00-\u9fa5]*
        # 常见在每页前300字符
        chaps = re.findall(r'(第[一二三四五六七八九十\d]+章[\u4e00-\u9fa5]{2,20}|导论[\u4e00-\u9fa5]{0,20})', text_clean[:300])
        for c in chaps:
            # 过滤非真正章节名
            if any(c.startswith(x) for x in ['第', '导论']):
                results.append((pnum, "CHAP", c))
                break
    return results

print("=== Scanning Q txt ===")
q_chaps = scan_chapters('backend/1000_q_txt')
seen = set()
for p, t, name in q_chaps:
    key = (t, name[:10])
    if key not in seen:
        seen.add(key)
        print(f"P{p:03d} [{t:6s}] {name}")

print("\n=== Scanning Exp txt ===")
exp_chaps = scan_chapters('backend/1000_exp_txt')
seen = set()
for p, t, name in exp_chaps:
    key = (t, name[:10])
    if key not in seen:
        seen.add(key)
        print(f"P{p:03d} [{t:6s}] {name}")
