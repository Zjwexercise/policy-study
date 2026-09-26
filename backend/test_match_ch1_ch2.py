import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def clean_ocr(text):
    prev = ""
    while prev != text:
        prev = text
        text = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', text)
    text = re.sub(r'([\u4e00-\u9fa5])\s+([，。！？；：、“”‘’（）《》【】])', r'\1\2', text)
    text = re.sub(r'([，。！？；：、“”‘’（）《》【】])\s+([\u4e00-\u9fa5])', r'\1\2', text)
    return text

def parse_questions_from_pages(folder, start_p, end_p):
    lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        for l in text.splitlines():
            l_s = l.strip()
            # 过滤页眉页脚
            if not l_s: continue
            if re.search(r'考研政治精雕细刻|第[一二三四五]部分|第[一二三四五六七八九十\d]+章|导论|^\d{1,3}$', l_s):
                continue
            lines.append(l_s)
            
    # 处理行倒置与题干切分
    # 题号匹配：开头是数字+点，或者是 l. / I. / 1 ．
    # 注意处理：
    # line i: "在分散的小农经济..."
    # line i+1: "4 ．"
    processed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # 检查 standalone 题号
        m_standalone = re.match(r'^([lI\d]{1,3})\s*[\.、．·:：]?$', line)
        if m_standalone and processed_lines:
            q_num = m_standalone.group(1).replace('l', '1').replace('I', '1')
            # 检查上一行是否不是选项
            prev = processed_lines.pop()
            if not re.match(r'^[A-Da-d①②③④]\s*[\.、．·:：]', prev):
                # 倒置了，把上一行接在题号后面
                processed_lines.append(f"{q_num}. {prev}")
            else:
                processed_lines.append(prev)
                processed_lines.append(f"{q_num}. ")
            i += 1
            continue
            
        # 标准化开头的 l. / I.
        line = re.sub(r'^[lI]\s*[\.、．·:：]\s*', '1. ', line)
        processed_lines.append(line)
        i += 1

    # 现在按题号切分题目
    full_text = "\n" + "\n".join(processed_lines)
    
    # 切分：换行后跟着数字 + 点 + 汉字/符号
    chunks = re.split(r'\n(?=\d{1,3}\s*[\.、．·:：])', full_text)
    
    questions = []
    for c in chunks:
        c = c.strip()
        if not c: continue
        m_head = re.match(r'^(\d{1,3})\s*[\.、．·:：]\s*([\s\S]+)', c)
        if not m_head: continue
        qnum = int(m_head.group(1))
        body = m_head.group(2).strip()
        
        # 寻找选项
        # 选项标准化
        def norm_opt(m):
            k = m.group(1).upper()
            if k in ['①', '1']: return '\nA. '
            if k in ['②', '2', '8', '13']: return '\nB. '
            if k in ['③', '3', '0', 'O']: return '\nC. '
            if k in ['④', '4', 'L)']: return '\nD. '
            return f'\n{k}. '

        body = re.sub(r'(?:^|\s+)([A-Da-d①②③④]|L\)|13)\s*[\.、．，,·:：\s]\s*', norm_opt, body)
        opt_matches = list(re.finditer(r'\n([A-D])\.\s*([\s\S]*?)(?=(?:\n[A-D]\.)|\Z)', body))
        
        if len(opt_matches) >= 2:
            stem = body[:opt_matches[0].start()].strip()
            stem = re.sub(r'[\s\n]+', ' ', stem).strip()
            
            opts = {}
            for om in opt_matches:
                k = om.group(1).upper()
                v = om.group(2).strip()
                v = re.sub(r'^[A-Da-d①②③④\(\)]\s*[\.、．，,·:\s]\s*', '', v)
                v = re.sub(r'\s*\d{1,3}\s*[\.、．·:：]\s*[\u4e00-\u9fa5].*$', '', v)
                v = re.sub(r'[\s\n]+', ' ', v).strip()
                if k in ['A', 'B', 'C', 'D'] and v:
                    opts[k] = v
                    
            final_opts = [{'key': k, 'value': opts[k]} for k in ['A', 'B', 'C', 'D'] if k in opts]
            if len(stem) >= 6 and len(final_opts) >= 2:
                questions.append({
                    'q_num': qnum,
                    'stem': stem,
                    'options': final_opts
                })
    return questions

def parse_explanations_from_pages(folder, start_p, end_p):
    lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        for l in text.splitlines():
            l_s = l.strip()
            if not l_s: continue
            if re.search(r'考研政治精雕细刻|第[一二三四五]部分|第[一二三四五六七八九十\d]+章|导论|^\d{1,3}$', l_s):
                continue
            lines.append(l_s)
            
    full_text = "\n" + "\n".join(lines)
    
    # 切分解析块
    # 模式：题目开始标志
    # 比如：\n(?=(?:\d{1,3}\s*[\.、．·:：\s]*)?(?:答案|爷案|答索|案|〕)?\s*[A-D]{1,4}\s*[〖（\[(【]解析)
    # 或者 \n(?=\d{1,3}\s*[\.、．·:：]\s*(?:答案|[A-D]))
    split_pattern = r'\n(?=(?:(?:\d{1,3}\s*[\.、．·:：\s]*)?(?:答案|爷案|答索|答对|案|〕)?\s*[A-Da-d]{1,4}\s*[〖（\[(【]解析)|(?:\d{1,3}\s*[\.、．·:：]\s*))'
    blocks = re.split(split_pattern, full_text)
    
    explanations = []
    current_num = 1
    for b in blocks:
        b = b.strip()
        if not b or '解析' not in b:
            continue
            
        # 提取题号、答案、解析
        # 模式1: (\d{1,3}) ... 答案 A 解析 ...
        # 模式2: 答案 A 解析 ...
        # 模式3: A 解析 ...
        m = re.search(r'(?:^|[\s\n])(?:(\d{1,3})\s*[\.、．·:：\s]*)?(?:答案|爷案|答索|答对|案|〕)?\s*([A-Da-d]{1,4})\s*[〖（\[(【]解析[〗）\])】]?([\s\S]*)', b)
        if m:
            num_str = m.group(1)
            ans = m.group(2).upper()
            exp_text = m.group(3).strip()
            
            if num_str:
                qnum = int(num_str)
            else:
                qnum = current_num
                
            clean_exp = re.sub(r'[\s\n]+', ' ', exp_text).strip()
            
            # 双重核验答案：如果在解析尾部有明确结论，可核对
            # 如 "应选 A 项" 或 "故应选 B、D 两项"
            explanations.append({
                'q_num': qnum,
                'answer': ans,
                'explanation': f"【肖秀荣1000题精解】{clean_exp}"
            })
            current_num = qnum + 1
            
    return explanations

print("=== Ch1 Test ===")
ch1_q = parse_questions_from_pages('backend/1000_q_txt', 4, 6)
ch1_exp = parse_explanations_from_pages('backend/1000_exp_txt', 3, 6)
print(f"Ch1: Q count = {len(ch1_q)}, Exp count = {len(ch1_exp)}")
for q in ch1_q:
    exp = next((e for e in ch1_exp if e['q_num'] == q['q_num']), None)
    ans = exp['answer'] if exp else 'MISSING'
    print(f"Q{q['q_num']:02d}: Ans={ans:4s} | Options={[o['key'] for o in q['options']]} | Stem={q['stem'][:30]}")
