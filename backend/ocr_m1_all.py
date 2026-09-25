import fitz
import subprocess
import os
import sys
import re
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from extract_m1_ground_truth import m1_exps

q_pdf_path = os.path.join('pdf', '27《优题库》 - 压缩版', '27《优题库》 - 压缩版', '（已压缩）27《优题库-试题拔高篇》.pdf')
doc_q = fitz.open(q_pdf_path)
temp_img = 'backend/temp_m1_page.png'
ocr_script = 'backend/ocr_test.ps1'

# Page 6 to 11 (index 5 to 10)
pages_text = []
for p in range(5, 11):
    pix = doc_q[p].get_pixmap(dpi=150)
    pix.save(temp_img)
    cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ocr_script, '-ImagePath', temp_img]
    res = subprocess.run(cmd, capture_output=True)
    txt = res.stdout.decode('utf-8', errors='ignore')
    pages_text.append(txt)
    print(f"Page {p+1} OCR done, lines: {len(txt.splitlines())}")

if os.path.exists(temp_img):
    os.remove(temp_img)

full_ocr = "\n".join(pages_text)
with open('backend/m1_raw_ocr.txt', 'w', encoding='utf-8') as f:
    f.write(full_ocr)

print("Saved raw OCR to backend/m1_raw_ocr.txt")
