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

def parse_module_explanations(folder, start_p, end_p):
    lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        for l in text.splitlines():
            l_s = l.strip()
            if not l_s: continue
            lines.append(l_s)

    # 寻找所有解析条目
    # 肖秀荣解析特点：包含“解析”并且有答案选项
    # 答案模式：答案/爷案/答索 + [A-D]+，或者 standalone [A-D]+ 〖解析〗
    exp_items = []
    
    # 正则表达式识别解析行
    # 匹配诸如:
    # "答案 B 〖解析〗"
    # "A 〖解析]"
    # "3 1 爷案 ) A [解析〗"
    # "4 案 〕 8 〖解析〗"
    # "10. 【答案】 ABD 【解析】"
    # "1 1• 1 爷搴 〕 BCD 〖解析〗"
    # "12 ． ． 答案》 ABC 〖解析〗"
    # "'BD 〖解析〗"
    pattern = re.compile(
        r'(?:(?:^|[\s\n])(\d{1,3})\s*[\.、．·:：•\s]*)?'
        r'(?:答案|爷案|答索|答对|爷搴|案|〕)?\s*'
        r'[\(\[<《\s]*([A-Da-d801]{1,4})[\)\]>》\s]*'
        r'[〖（\[(【]解析[〗）\])】]?'
    )

    starts = []
    for i, line in enumerate(lines):
        # 排除包含“解析”但不是解析起始的句子，如“关于解析”
        m = pattern.search(line)
        if m:
            qnum_str = m.group(1)
            ans = m.group(2).upper()
            # 替换 OCR 错误：8 -> B, 0 -> C
            ans_clean = ""
            for ch in ans:
                if ch == '8': ans_clean += 'B'
                elif ch == '0': ans_clean += 'C'
                elif ch == '1': ans_clean += 'A'
                elif ch in 'ABCD': ans_clean += ch
            if not ans_clean: continue
            
            # 检查上一行是否有 standalone 题号
            if not qnum_str and i > 0:
                m_prev = re.match(r'^(\d{1,3})\s*[\.、．·:：]?$', lines[i-1])
                if m_prev:
                    qnum_str = m_prev.group(1)
            starts.append((i, int(qnum_str) if qnum_str else None, ans_clean, line))

    for idx, (start_idx, qnum, ans, line) in enumerate(starts):
        end_idx = starts[idx+1][0] if idx+1 < len(starts) else len(lines)
        chunk_lines = lines[start_idx:end_idx]
        full_chunk = " ".join(chunk_lines)
        # 移除解析标记前缀
        body = pattern.sub('', full_chunk, count=1).strip()
        body = re.sub(r'^[〖（\[(【]解析[〗）\])】]?\s*', '', body).strip()
        body = re.sub(r'[\s\n]+', ' ', body).strip()
        
        # 再次在解析正文尾部提取结论以校准答案
        # 比如：应选 A 项 / 故应选 B、D 两项 / BCD 是正确选项 / 故 C 项正确
        m_concl = re.search(r'(?:应选|故选|故应选|正确(?:选项|答案)是?)\s*([A-D](?:[、\s,与和]+[A-D])*)\s*(?:两|三|四)?项?', body)
        if m_concl:
            concl_ans = "".join(re.findall(r'[A-D]', m_concl.group(1)))
            if concl_ans and concl_ans != ans:
                # 采信结论中的答案
                ans = concl_ans

        exp_items.append({
            'index': idx + 1,
            'qnum': qnum,
            'answer': ans,
            'explanation': f"【肖秀荣1000题精解】{body}"
        })
        
    return exp_items

exp_m1 = parse_module_explanations('backend/1000_exp_txt', 3, 66)
print(f"Total Explanations in M1 (马原): {len(exp_m1)}")
valid_ans = sum(1 for e in exp_m1 if re.match(r'^[A-D]+$', e['answer']))
print(f"Valid answer keys: {valid_ans} / {len(exp_m1)}")
for e in exp_m1[:10]:
    print(f"#{e['index']:3d} | Ans={e['answer']:4s} | Exp: {e['explanation'][:60]}")
print("...")
for e in exp_m1[-5:]:
    print(f"#{e['index']:3d} | Ans={e['answer']:4s} | Exp: {e['explanation'][:60]}")
