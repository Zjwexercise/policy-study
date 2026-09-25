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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR_SCRIPT = os.path.join(BASE_DIR, "backend", "ocr_test.ps1")
Q_PDF = os.path.join(BASE_DIR, "pdf", "2027--1000题--试题册.pdf")

def ocr_page(doc, p, temp_img):
    pix = doc[p].get_pixmap(dpi=140)
    pix.save(temp_img)
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", OCR_SCRIPT, "-ImagePath", temp_img]
    res = subprocess.run(cmd, capture_output=True)
    try:
        txt = res.stdout.decode('utf-8')
    except Exception:
        txt = res.stdout.decode('gbk', errors='ignore')
    txt = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', txt)
    txt = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', txt)
    return txt

def main():
    doc = fitz.open(Q_PDF)
    temp_img = "backend/sample_page.png"
    
    full_text = ""
    for p in range(3, 15): # pages 4 to 15
        full_text += f"\n=== Page {p+1} ===\n" + ocr_page(doc, p, temp_img)
        
    doc.close()
    if os.path.exists(temp_img):
        os.remove(temp_img)
        
    # 切分题目
    pattern = re.compile(r'\n(?=\s*\d{1,3}\s*[\.、．，,\s]\s*[\u4e00-\u9fa5“\"\'《])')
    chunks = pattern.split(full_text)
    
    print(f"在试题册第 4~15 页共提取到 {len(chunks)} 个题目块：")
    valid_qs = 0
    for c in chunks:
        m = re.match(r'^\s*(\d{1,3})\s*[\.、．，,\s]\s*([\s\S]+)', c.strip())
        if m:
            num = int(m.group(1))
            body = m.group(2)
            # 查找选项
            if any(opt in body for opt in ['A.', 'A ．', 'A ', 'B.', 'B ．', 'B ']):
                valid_qs += 1
                if valid_qs <= 10:
                    lines = [l.strip() for l in body.splitlines() if l.strip()]
                    print(f"  Q{num}: {lines[0][:60]}")
    print(f"有效选择题总数: {valid_qs}")

if __name__ == "__main__":
    main()
