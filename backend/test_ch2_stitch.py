import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def clean_ocr(text):
    prev = ""
    while prev != text:
        prev = text
        text = re.sub(r'([\u4e00-\u9fa5])[ \t]+([\u4e00-\u9fa5])', r'\1\2', text)
        text = re.sub(r'([\u4e00-\u9fa5])[ \t]+([^\w\s])', r'\1\2', text)
        text = re.sub(r'([^\w\s])[ \t]+([\u4e00-\u9fa5])', r'\1\2', text)
    return text

def get_clean_chapter_lines(folder, start_p, end_p):
    all_lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        raw_lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        # 移除页首的页眉 (前3行中匹配模块/章节/书名)
        start_idx = 0
        while start_idx < min(4, len(raw_lines)):
            l = raw_lines[start_idx]
            if re.search(r'考研政治精雕细刻|第[一二三四五]部分|第[一二三四五六七八九十\d]+章|导论|世界的物质性|^[一二三四]、[单多]项选择题$|^[总一早]$', l):
                start_idx += 1
            else:
                break
                
        # 移除页尾的页码 (最后1行如果是纯数字)
        end_idx = len(raw_lines)
        if end_idx > start_idx and re.match(r'^\d{1,3}$', raw_lines[-1]):
            end_idx -= 1
            
        page_lines = raw_lines[start_idx:end_idx]
        all_lines.extend(page_lines)
        
    return all_lines

lines = get_clean_chapter_lines('backend/1000_q_txt', 7, 16)
print(f"Total stitched lines in Ch2: {len(lines)}")
for i, l in enumerate(lines[:30]):
    print(f"{i+1:2d}: {l[:60]}")
