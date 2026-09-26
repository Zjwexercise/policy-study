import fitz
import os
import subprocess
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR_SCRIPT = os.path.join(BASE_DIR, 'backend', 'ocr_test.ps1')
YOUTIKU_Q_PDF = os.path.join(BASE_DIR, 'pdf', '27《优题库》 - 压缩版', '27《优题库》 - 压缩版', '（已压缩）27《优题库-试题拔高篇》.pdf')
doc = fitz.open(YOUTIKU_Q_PDF)
temp_img = os.path.join(BASE_DIR, 'backend', 'temp_p.png')

targets = [87, 88, 93, 94, 99, 100, 105, 106, 111, 112, 117, 118, 123, 124, 128, 129]

for p in targets:
    if p < len(doc):
        doc[p].get_pixmap(dpi=140).save(temp_img)
        cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', OCR_SCRIPT, '-ImagePath', temp_img]
        raw = subprocess.run(cmd, capture_output=True).stdout.decode('utf-8', errors='ignore')
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        header = " /// ".join(lines[:3])
        print(f"Page {p+1:3d}: {header}", flush=True)

if os.path.exists(temp_img):
    os.remove(temp_img)
