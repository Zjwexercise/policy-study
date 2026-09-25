import fitz
import os
import sys
import re
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR_SCRIPT = os.path.join(BASE_DIR, "backend", "ocr_test.ps1")
Q_PDF = os.path.join(BASE_DIR, "pdf", "2027-刷题计划--试题册.pdf")
EXP_PDF = os.path.join(BASE_DIR, "pdf", "2027-刷题计划--解析册.pdf")

def ocr_page(doc, page_num, temp_img):
    pix = doc[page_num].get_pixmap(dpi=140)
    pix.save(temp_img)
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", OCR_SCRIPT, "-ImagePath", temp_img]
    proc = subprocess.run(cmd, capture_output=True)
    try:
        raw = proc.stdout.decode('utf-8')
    except Exception:
        raw = proc.stdout.decode('gbk', errors='ignore')
    # 清理空格
    raw = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', raw)
    raw = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', raw)
    return raw

def main():
    doc_q = fitz.open(Q_PDF)
    temp_img = "backend/sample_page.png"
    
    # 扫描试题册前 5 页 (Page 3~7)
    txt_q = ""
    for p in range(2, 7):
        txt_q += f"\n=== Page {p+1} ===\n" + ocr_page(doc_q, p, temp_img)
        
    doc_q.close()
    if os.path.exists(temp_img):
        os.remove(temp_img)
        
    # 提取题目
    pattern = re.compile(r'\n(?=\s*\d{1,3}\s*[\.、．，,]\s*[\u4e00-\u9fa5“\"\'《])')
    chunks = pattern.split(txt_q)
    print(f"试题册前 5 页成功提取到 {len(chunks)} 个题目块：")
    for i, c in enumerate(chunks[:8]):
        lines = [l.strip() for l in c.splitlines() if l.strip()]
        if lines:
            print(f"[{i}] {lines[0][:60]}")

if __name__ == "__main__":
    main()
