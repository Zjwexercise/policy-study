import re
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

with open('backend/st_p13_25.txt', encoding='utf-8') as f:
    txt = f.read()

# Normalize spaces between chinese characters if not already done
# Actually st_p13_25.txt has spaces like "马 克 思 主 义" on some lines.
# Let's inspect line 9 of st_p13_25.txt:
# "1. 习 近 平 总 书 记 在 二 十 大 报 告 中 强 调 ： “ 马 克 思 主 义 是 我 们 立 党 立 国"
# Notice OCR had single space between each Chinese character!

def clean_ocr_text(text: str) -> str:
    # Collapse spaces between Chinese characters
    # Do it repeatedly until stable
    prev = ""
    curr = text
    while curr != prev:
        prev = curr
        curr = re.sub(r'([\u4e00-\u9fa5“\"\'《（(、，。：；！？])\s+([\u4e00-\u9fa5”\"\'》）)、，。：；！？])', r'\1\2', curr)
    return curr

cleaned = clean_ocr_text(txt)

pattern = re.compile(r'\n(?=\s*\d{1,2}\s*[\.、．，,]\s*[\u4e00-\u9fa5“\"\'《])')
chunks = pattern.split(cleaned)
print(f"Total chunks: {len(chunks)}")

parsed = []
for i, c in enumerate(chunks):
    m = re.match(r'^\s*(\d{1,2})\s*[\.、．，,]\s*([\s\S]+)', c.strip())
    if not m:
        continue
    num = int(m.group(1))
    body = m.group(2)
    
    # find answer
    ans_m = re.search(r'(?:〖?\s*答案\s*〗?|【?\s*答案\s*】?|答案\s*[:：]|〖\s*答案)\s*([A-Da-d]+)', body)
    if not ans_m:
        continue
    ans = ans_m.group(1).upper()
    
    stem_and_opts = body[:ans_m.start()].strip()
    explanation = body[ans_m.end():].strip()
    explanation = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[\u4e00-\u9fa5]|$)', '', explanation)
    explanation = re.sub(r'^[^\u4e00-\u9fa5]+', '', explanation)
    explanation = re.sub(r'[\s\n]+', ' ', explanation).strip()
    
    # Find options
    # Notice options in st_p13_25:
    # A ． xxx B ． xxx C ． xxx D ． xxx
    opt_re = re.compile(r'(?:^|\n|\s+)([A-D])\s*[\.、．，,·\s]\s*([\s\S]*?)(?=(?:(?:\n|\s+)[A-D]\s*[\.、．，,·\s])|\Z)')
    opt_matches = list(opt_re.finditer(stem_and_opts))
    
    if len(opt_matches) >= 2:
        stem = stem_and_opts[:opt_matches[0].start()].strip()
        stem = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[\u4e00-\u9fa5]|$)', '', stem)
        stem = re.sub(r'[\s\n]+', ' ', stem).strip()
        
        opts = []
        for om in opt_matches:
            k = om.group(1)
            v = om.group(2).strip()
            v = re.sub(r'[\s\n]+', ' ', v).strip()
            opts.append({'key': k, 'value': v})
            
        parsed.append({
            'num': num,
            'ans': ans,
            'stem': stem,
            'opts': opts,
            'exp': explanation
        })

print(f"Successfully parsed {len(parsed)} questions!")
for i, p in enumerate(parsed):
    opt_keys = "".join([o['key'] for o in p['opts']])
    print(f"{i+1:2d}. Q{p['num']:2d} [{p['ans']}] (Opts: {opt_keys}) | {p['stem'][:50]}")

