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

def parse_chapter_explanations(folder, start_p, end_p):
    lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        for l in text.splitlines():
            l_s = l.strip()
            if not l_s: continue
            # 过滤纯页码或页眉
            if re.search(r'考研政治精雕细刻|第[一二三四五]部分|第[一二三四五六七八九十\d]+章|导论|^\d{1,3}$', l_s):
                # 只有当整行就是标题才过滤
                if len(l_s) < 25 and any(x in l_s for x in ['第', '导论', '考研政治']):
                    continue
            lines.append(l_s)

    # 识别每个解析项的起始行
    # 特征：包含 "解析" 并且在这一行或前一行有答案和题号
    # 模式匹配解析起始
    exp_starts = []
    for i, line in enumerate(lines):
        # 寻找诸如:
        # "答案 B （解析 〗"
        # "A 〖 解析 ]"
        # "3 1 爷案 ) A [ 解析 〗"
        # "4 ． D 〖 解析 〗"
        # "10. 【答案】 ABD 【解析】"
        # "1 1• 1 爷搴 〕 BCD 〖 解析 〗"
        # "12 ． ． 答案》 ABC 〖 解析 〗"
        # "'BD 〖 解析 〗"
        m = re.search(r'(?:(?:^|[\s\n])(\d{1,3})\s*[\.、．·:：•\s]*)?(?:答案|爷案|答索|答对|爷搴|案|〕)?\s*[\(\[<《\s]*([A-Da-d]{1,4})[\)\]>》\s]*[〖（\[(【]解析[〗）\])】]?', line)
        if m:
            qnum_str = m.group(1)
            ans = m.group(2).upper()
            # 检查前一行是否是 standalone 题号，如 "4 ．"
            if not qnum_str and i > 0:
                m_prev = re.match(r'^(\d{1,3})\s*[\.、．·:：]?$', lines[i-1])
                if m_prev:
                    qnum_str = m_prev.group(1)
            exp_starts.append((i, qnum_str, ans, line))

    exps = []
    for idx, (start_line_idx, qnum_str, ans, line) in enumerate(exp_starts):
        end_line_idx = exp_starts[idx + 1][0] if idx + 1 < len(exp_starts) else len(lines)
        exp_content_lines = lines[start_line_idx:end_line_idx]
        exp_full = " ".join(exp_content_lines)
        # 剥离题头
        exp_clean = re.sub(r'^(?:\d{1,3}\s*[\.、．·:：•\s]*)?(?:答案|爷案|答索|答对|爷搴|案|〕)?\s*[\(\[<《\s]*[A-Da-d]{1,4}[\)\]>》\s]*[〖（\[(【]解析[〗）\])】]?', '', exp_full).strip()
        exps.append({
            'index': idx + 1,
            'qnum_found': int(qnum_str) if qnum_str else None,
            'answer': ans,
            'explanation': f"【肖秀荣1000题精解】{exp_clean}"
        })
    return exps

exps = parse_chapter_explanations('backend/1000_exp_txt', 3, 6)
print(f"Total explanations found: {len(exps)}")
for e in exps:
    print(f"Index {e['index']:2d} (Q{str(e['qnum_found']):4s}) | Ans={e['answer']:4s} | Exp={e['explanation'][:60]}")
