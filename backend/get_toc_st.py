import fitz
import os
import subprocess
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

pdf_path = 'pdf/2027-考研政治刷题计划.pdf'
doc = fitz.open(pdf_path)
print(f"Total pages: {len(doc)}")

OCR_SCRIPT = "backend/ocr_test.ps1"
temp_img = "backend/temp_toc.png"

for p in range(12):
    pix = doc[p].get_pixmap(dpi=140)
    pix.save(temp_img)
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", OCR_SCRIPT, "-ImagePath", temp_img]
    proc = subprocess.run(cmd, capture_output=True)
    try:
        txt = proc.stdout.decode('utf-8')
    except Exception:
        txt = proc.stdout.decode('gbk', errors='ignore')
    
    first_lines = [l.strip() for l in txt.splitlines() if l.strip()][:5]
    print(f"Page {p+1}: {' / '.join(first_lines)}")

if os.path.exists(temp_img):
    os.remove(temp_img)
