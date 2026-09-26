import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def clean_ocr(text):
    prev = ""
    while prev != text:
        prev = text
        text = re.sub(r'([\u4e00-\u9fa5])[ \t]+([\u4e00-\u9fa5])', r'\1\2', text)
        text = re.sub(r'([\u4e00-\u9fa5])[ \t]+([^\w\s])', r'\1\2', text)
        text = re.sub(r'([^\w\s])[ \t]+([\u4e00-\u9fa5])', r'\1\2', text)
    return text

def parse_ch_explanations(folder, start_p, end_p):
    lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        for l in text.splitlines():
            l_s = l.strip()
            if not l_s: continue
            if len(l_s) < 30 and re.search(r'考研政治精雕细刻|第[一二三四五]部分|第[一二三四五六七八九十\d]+章|导论|^\d{1,3}$|^[一二三四]、[单多]项选择题$', l_s):
                continue
            lines.append(l_s)

    # 寻找解析开始
    # 模式：
    # 答案 [A-D]+ 〖解析〗
    # (\d{1,3}) ... 答案 [A-D]+ 〖解析〗
    # (\d{1,3}) ... [A-D]+ 〖解析〗
    # [A-D]+ 〖解析〗
    exp_starts = []
    for i, line in enumerate(lines):
        m = re.search(r'(?:(?:^|[\s\n])(\d{1,3})\s*[\.、．·:：•\s]*)?(?:答案|爷案|答索|答对|爷搴|案|〕)?\s*[\(\[<《\s]*([A-Da-d]{1,4})[\)\]>》\s]*[〖（\[(【]解析[〗）\])】]?', line)
        if m:
            num_str = m.group(1)
            ans = m.group(2).upper()
            if not num_str and i > 0:
                m_prev = re.match(r'^(\d{1,3})\s*[\.、．·:：]?$', lines[i-1])
                if m_prev:
                    num_str = m_prev.group(1)
            exp_starts.append((i, num_str, ans, line))

    exps = []
    for idx, (start_line_idx, qnum_str, ans, line) in enumerate(exp_starts):
        end_line_idx = exp_starts[idx + 1][0] if idx + 1 < len(exp_starts) else len(lines)
        exp_content_lines = lines[start_line_idx:end_line_idx]
        exp_full = " ".join(exp_content_lines)
        exp_clean = re.sub(r'^(?:\d{1,3}\s*[\.、．·:：•\s]*)?(?:答案|爷案|答索|答对|爷搴|案|〕)?\s*[\(\[<《\s]*[A-Da-d]{1,4}[\)\]>》\s]*[〖（\[(【]解析[〗）\])】]?', '', exp_full).strip()
        exps.append({
            'index': idx + 1,
            'qnum_found': int(qnum_str) if qnum_str else None,
            'answer': ans,
            'explanation': f"【肖秀荣1000题精解】{exp_clean}",
            'raw_first_line': line
        })
    return exps

# 马原第2章: 世界的物质性及发展规律
# Exp begins on page 6 bottom, goes up to page 17
ch2_exps = parse_ch_explanations('backend/1000_exp_txt', 6, 17)
print(f"Total Ch2 Explanations found: {len(ch2_exps)}")
for e in ch2_exps[:15]:
    print(f"#{e['index']:2d} (Q{str(e['qnum_found']):4s}) | Ans={e['answer']:4s} | {e['raw_first_line'][:50]}")
