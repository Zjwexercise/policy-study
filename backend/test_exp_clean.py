import re
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def clean_ocr_spaces(text):
    # 多次循环消除中文字符之间的空格
    prev = ""
    while prev != text:
        prev = text
        text = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', text)
    # 处理中文字符与中文标点之间的空格
    text = re.sub(r'([\u4e00-\u9fa5])\s+([，。！？；：、“”‘’（）《》【】])', r'\1\2', text)
    text = re.sub(r'([，。！？；：、“”‘’（）《》【】])\s+([\u4e00-\u9fa5])', r'\1\2', text)
    return text

with open('backend/1000_exp_txt/page_003.txt', 'r', encoding='utf-8-sig') as f:
    raw = f.read()

cleaned = clean_ocr_spaces(raw)
print("=== Cleaned Page 3 ===")
for line in cleaned.splitlines()[:20]:
    if line.strip():
        print(line)
