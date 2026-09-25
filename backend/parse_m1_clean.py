import re
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from extract_m1_ground_truth import m1_exps

with open('backend/m1_raw_ocr.txt', 'r', encoding='utf-8') as f:
    raw_ocr = f.read()

# 预处理：修复中文字符间空格、常见 OCR 符号
lines = []
for l in raw_ocr.splitlines():
    l = l.strip()
    if not l:
        continue
    # 修复常见前缀如 & 形式与内容的关系 -> B. 形式与内容的关系
    l = re.sub(r'^&\s*', 'B. ', l)
    l = re.sub(r'^[oO0]\s*[\.、．，,·:\s]\s*', 'C. ', l)
    # 合并汉字间的空格
    for _ in range(3):
        l = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', l)
    lines.append(l)

clean_text = "\n".join(lines)

# 寻找题号切分点 1~30
# 匹配开头的数字
q_starts = []
target_q = 1
for idx, l in enumerate(lines):
    m = re.match(r'^(\d{1,2})\s*[·\.、．，,\s]\s*(.*)', l)
    if m:
        num = int(m.group(1))
        if num == target_q:
            q_starts.append((num, idx))
            target_q += 1

print(f"Matched {len(q_starts)} questions sequentially:")
for num, idx in q_starts:
    print(f"  Q{num}: line {idx+1}: {lines[idx][:40]}")

questions_data = []
for i, (qnum, start_idx) in enumerate(q_starts):
    end_idx = q_starts[i+1][1] if i+1 < len(q_starts) else len(lines)
    chunk_lines = lines[start_idx:end_idx]
    
    # 第一行去掉题号
    chunk_lines[0] = re.sub(r'^\d{1,2}\s*[·\.、．，,\s]\s*', '', chunk_lines[0])
    chunk_text = "\n".join(chunk_lines)
    
    # 统一规范选项前缀 A. B. C. D.
    chunk_text = re.sub(r'(?:^|\n|\s+)([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\s*[\.、．，,·:\s]\s*', r'\n\1. ', chunk_text)
    
    # 提取选项
    opt_matches = list(re.finditer(r'\n([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\.\s*([\s\S]*?)(?=(?:\n[A-Da-dＡ-Ｄａ-ｄ①②③④]\.)|\Z)', chunk_text))
    
    if opt_matches:
        stem = chunk_text[:opt_matches[0].start()].strip()
        stem = re.sub(r'[\s\n]+', ' ', stem).strip()
        
        opts_dict = {}
        for om in opt_matches:
            k = om.group(1).upper()
            if k in ['①', '1']: k = 'A'
            elif k in ['②', '2']: k = 'B'
            elif k in ['③', '3']: k = 'C'
            elif k in ['④', '4']: k = 'D'
            k = k.replace('(', '').replace(')', '').strip()
            if k in ['Ａ']: k = 'A'
            elif k in ['Ｂ']: k = 'B'
            elif k in ['Ｃ']: k = 'C'
            elif k in ['Ｄ']: k = 'D'
            
            v = re.sub(r'[\s\n]+', ' ', om.group(2)).strip()
            v = re.sub(r'^[A-D]\.\s*', '', v)
            if k in ['A', 'B', 'C', 'D'] and v:
                opts_dict[k] = v
                
        final_opts = [{'key': k, 'value': opts_dict[k]} for k in ['A', 'B', 'C', 'D'] if k in opts_dict]
    else:
        stem = chunk_text.strip()
        final_opts = []
        
    gt = m1_exps.get(qnum, {})
    ans = gt.get('answer', 'A')
    exp = gt.get('explanation', '')
    
    questions_data.append({
        'qnum': qnum,
        'stem': f"【综合测试一】{stem}",
        'options': final_opts,
        'answer': ans,
        'explanation': exp,
        'type': 'multiple' if len(ans) > 1 else 'single',
        'category': '马原'
    })

print(f"\nSuccessfully parsed {len(questions_data)} questions!")
for q in questions_data:
    opt_lens = len(q['options'])
    keys = [o['key'] for o in q['options']]
    if opt_lens != 4:
        print(f"⚠️ Q{q['qnum']}: {opt_lens} options: {keys} | Stem: {q['stem'][:40]}")
    else:
        print(f"✅ Q{q['qnum']}: 4 options {keys} | Ans: {q['answer']} | Stem: {q['stem'][:35]}")
