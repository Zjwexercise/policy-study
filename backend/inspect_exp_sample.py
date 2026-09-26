import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def clean_ocr_spaces(text):
    prev = ""
    while prev != text:
        prev = text
        text = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', text)
    text = re.sub(r'([\u4e00-\u9fa5])\s+([，。！？；：、“”‘’（）《》【】])', r'\1\2', text)
    text = re.sub(r'([，。！？；：、“”‘’（）《》【】])\s+([\u4e00-\u9fa5])', r'\1\2', text)
    return text

for p in range(3, 8):
    fname = f'backend/1000_exp_txt/page_{p:03d}.txt'
    with open(fname, 'r', encoding='utf-8-sig') as f:
        raw = f.read()
    cleaned = clean_ocr_spaces(raw)
    print(f"\n=================== PAGE {p} ===================")
    for line in cleaned.splitlines():
        line = line.strip()
        if not line: continue
        # 如果包含解析或者答案
        if any(w in line for w in ['解析', '答案', '爷案', '选项', '【', '〖', '[']) or re.search(r'^\d{1,3}\b', line):
            print(line[:120])
