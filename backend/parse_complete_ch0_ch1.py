import re
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load both files
with open('backend/st_p13_25.txt', encoding='utf-8') as f:
    t1 = f.read()
with open('backend/st_p26_35.txt', encoding='utf-8') as f:
    t2 = f.read()

full_raw = t1 + "\n" + t2

def clean_ocr_text(text: str) -> str:
    prev = ""
    curr = text
    while curr != prev:
        prev = curr
        curr = re.sub(r'([\u4e00-\u9fa5“\"\'《（(、，。：；！？])\s+([\u4e00-\u9fa5”\"\'》）)、，。：；！？])', r'\1\2', curr)
    return curr

cleaned = clean_ocr_text(full_raw)

# Let's inspect sections in cleaned text
# 1. 导论 考纲基础 (Single: Q1-Q8, Multi: Q9-Q15)
# 2. 导论 仿真提高 (Single: Q1-Q6, Multi: Q7-Q9)
# 3. 第一章 世界的物质性及其发展规律 考纲基础 (Single: Q1-Q10, Multi: Q11-Q25)
# 4. 第一章 仿真提高 (Single: Q1-Q16, Multi: Q17-Q33)

print("Text length:", len(cleaned))

# Let's find all question blocks by identifying numbered questions
# Pattern: line starts with e.g. "1. " or "1 ． "
pattern = re.compile(r'\n(?=\s*\d{1,2}\s*[\.、．，,·]\s*[\u4e00-\u9fa5“\"\'《（(])')
chunks = pattern.split(cleaned)
print(f"Total raw chunks: {len(chunks)}")

def clean_opt_val(v: str) -> str:
    # remove inline distractor explanations if attached, e.g. "马 克 思 主 义 提 供 的 是 方 法 论..."
    # actually, in clean_options.py, there are routines. Let's do basic cleanup first
    v = re.sub(r'^[A-Da-d\(\)①②③④]\s*[\.、．，,·:\s]\s*', '', v)
    v = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[A-Za-z\u4e00-\u9fa5]|$)', '', v)
    v = re.sub(r'[\s\n]+', ' ', v).strip()
    return v

parsed_qs = []
for idx, c in enumerate(chunks):
    c = c.strip()
    m = re.match(r'^\s*(\d{1,2})\s*[\.、．，,·]\s*([\s\S]+)', c)
    if not m:
        continue
    num = int(m.group(1))
    body = m.group(2)
    
    # Check if there is an answer
    ans_m = re.search(r'(?:〖?\s*答\s*案\s*〗?|【?\s*答\s*案\s*】?|答\s*案\s*[:：]|〖\s*答\s*案)\s*([A-Da-d]+)', body)
    if not ans_m:
        continue
    ans = ans_m.group(1).upper()
    
    stem_and_opts = body[:ans_m.start()].strip()
    explanation = body[ans_m.end():].strip()
    explanation = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[\u4e00-\u9fa5]|$)', '', explanation)
    explanation = re.sub(r'^[^\u4e00-\u9fa5]+', '', explanation)
    explanation = re.sub(r'[\s\n]+', ' ', explanation).strip()
    
    # Match options
    opt_re = re.compile(r'(?:^|\n|\s+)([A-D])\s*[\.、．，,·\s]\s*([\s\S]*?)(?=(?:(?:\n|\s+)[A-D]\s*[\.、．，,·\s])|\Z)')
    opt_matches = list(opt_re.finditer(stem_and_opts))
    
    if len(opt_matches) >= 2:
        stem = stem_and_opts[:opt_matches[0].start()].strip()
        stem = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[\u4e00-\u9fa5]|$)', '', stem)
        stem = re.sub(r'[\s\n]+', ' ', stem).strip()
        
        opts = []
        for om in opt_matches:
            k = om.group(1)
            v = clean_opt_val(om.group(2))
            opts.append({'key': k, 'value': v})
            
        parsed_qs.append({
            'num': num,
            'ans': ans,
            'stem': stem,
            'opts': opts,
            'exp': explanation,
            'raw': c[:100]
        })

print("Saved to backend/parsed_ch0_ch1.json")
for i, q in enumerate(parsed_qs):
    opt_k = "".join([o['key'] for o in q['opts']])
    print(f"{i+1:2d}. Q{q['num']:2d} [{q['ans']:4s}] (Opts: {opt_k:4s}) | {q['stem'][:45]}")

