import fitz
import subprocess
import re
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

doc = fitz.open('pdf/2027--1000题--解析册.pdf')
temp_img = 'backend/sample_page.png'

for p in range(2, 9): # pages 3 to 9 of 解析册
    pix = doc[p].get_pixmap(dpi=140)
    pix.save(temp_img)
    cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'backend/ocr_test.ps1', '-ImagePath', temp_img]
    res = subprocess.run(cmd, capture_output=True)
    try:
        txt = res.stdout.decode('utf-8')
    except Exception:
        txt = res.stdout.decode('gbk', errors='ignore')
    txt = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', txt)
    txt = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', txt)
    
    # 查找所有答案与题号
    print(f"=== 解析册 Page {p+1} ===")
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    for l in lines:
        if "答案" in l or "解析" in l or re.match(r'^\d{1,3}\s*[\.、．，,\s]', l):
            print(f"   {l[:60]}")

if os.path.exists(temp_img):
    os.remove(temp_img)
