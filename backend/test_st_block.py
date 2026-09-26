import fitz
import subprocess
import os
import sys
import re

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

p = os.path.join('pdf', '2027-考研政治刷题计划.pdf')
doc = fitz.open(p)
temp_img = 'backend/temp_st_test.png'
ocr_script = 'backend/ocr_test.ps1'

# OCR pages 13 to 17 (index 12 to 16)
pages_text = []
for pg in range(12, 17):
    pix = doc[pg].get_pixmap(dpi=150)
    pix.save(temp_img)
    cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ocr_script, '-ImagePath', temp_img]
    res = subprocess.run(cmd, capture_output=True)
    raw = res.stdout.decode('utf-8', errors='ignore')
    # clean line
    clean_lines = []
    for l in raw.splitlines():
        l = l.strip()
        if not l: continue
        for _ in range(3):
            l = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', l)
        clean_lines.append(l)
    pages_text.append("\n".join(clean_lines))

if os.path.exists(temp_img):
    os.remove(temp_img)

full_ocr = "\n".join(pages_text)

# 按照形如 \n\d{1,2} ． 或 \n\d{1,2} . 切分题目
# 注意标点：. ． 、 ·
q_chunks = re.split(r'\n(?=\s*\d{1,2}\s*[·\.、．，,\s]\s*[\u4e00-\u9fa5“\"\'《])', full_ocr)
print(f"Total chunks matched: {len(q_chunks)}")

for idx, c in enumerate(q_chunks):
    c = c.strip()
    # 查找答案标记
    ans_m = re.search(r'(?:〖?\s*答案\s*〗?|【?\s*答案\s*】?|答案\s*[:：])\s*([A-Da-d]+)', c)
    if not ans_m:
        continue
    ans = ans_m.group(1).upper()
    pre_ans = c[:ans_m.start()].strip()
    post_ans = c[ans_m.end():].strip()
    
    # 提取题号与题干
    m_num = re.match(r'^\s*(\d{1,2})\s*[·\.、．，,\s]\s*([\s\S]+)', pre_ans)
    if not m_num:
        continue
    qnum = int(m_num.group(1))
    body = m_num.group(2)
    
    # 提取选项
    body = re.sub(r'(?:^|\n|\s+)([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\s*[\.、．，,·:\s]\s*', r'\n\1. ', body)
    opt_matches = list(re.finditer(r'\n([A-D])\.\s*([\s\S]*?)(?=(?:\n[A-D]\.)|\Z)', body))
    
    stem = body[:opt_matches[0].start()].strip() if opt_matches else body
    opts = {}
    for om in opt_matches:
        k = om.group(1).upper()
        v = re.sub(r'[\s\n]+', ' ', om.group(2)).strip()
        opts[k] = v
        
    print("="*60)
    print(f"Q{qnum} | Ans: {ans}")
    print(f"Stem: {stem[:50]}...")
    print(f"Options ({len(opts)}): {opts}")
    print(f"Exp: {post_ans[:60]}...")
