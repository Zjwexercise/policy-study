import fitz
import os
import sys
import subprocess
import re

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    doc = fitz.open('pdf/27《优题库》 - 压缩版/27《优题库》 - 压缩版/（已压缩）27《优题库-试题拔高篇》.pdf')
    temp_img = 'backend/sample_page.png'

    full_txt = ''
    for p in range(5, 11): # pages 6 to 11
        pix = doc[p].get_pixmap(dpi=140)
        pix.save(temp_img)
        cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'backend/ocr_test.ps1', '-ImagePath', temp_img]
        res = subprocess.run(cmd, capture_output=True)
        try:
            txt = res.stdout.decode('utf-8')
        except Exception:
            txt = res.stdout.decode('gbk', errors='ignore')
        full_txt += f'\n=== Page {p+1} ===\n' + txt

    if os.path.exists(temp_img):
        os.remove(temp_img)

    # 清理空格
    full_txt = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', full_txt)
    full_txt = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', full_txt)

    # 查找题目
    q_matches = re.findall(
        r'(?:^|\n)\s*(\d{1,2})\s*[\.、．]\s*([\u4e00-\u9fa5“\"\'《][\s\S]*?)(?=(?:\n\s*\d{1,2}\s*[\.、．]\s*[\u4e00-\u9fa5“\"\'《])|\Z)',
        full_txt
    )
    print(f"在第 6~11 页（综合测试一）共识别到 {len(q_matches)} 道题目：")
    for num, q_text in q_matches:
        print(f"Q{num}: {q_text[:70].replace(chr(10), ' ')}")

if __name__ == "__main__":
    main()
