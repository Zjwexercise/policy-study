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

def get_chapter_lines(folder, start_p, end_p):
    all_lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        for l in text.splitlines():
            l_s = l.strip()
            if not l_s: continue
            # 过滤纯页眉和页脚
            if len(l_s) < 30 and re.search(r'考研政治精雕细刻|第[一二三四五]部分|第[一二三四五六七八九十\d]+章|导论|^\d{1,3}$|^[一二三四]、[单多]项选择题$', l_s):
                continue
            all_lines.append(l_s)
    return all_lines

def parse_robust_questions(lines):
    # 处理倒置
    processed = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # 单独的题号
        m_num = re.match(r'^([lI\d]{1,3})\s*[\.、．·:：]?$', line)
        if m_num and processed:
            num_val = m_num.group(1).replace('l', '1').replace('I', '1')
            prev = processed.pop()
            if not re.match(r'^[A-Da-d①②③④80oO]\s*[\.、．·:：\s]', prev):
                processed.append(f"{num_val}. {prev}")
            else:
                processed.append(prev)
                processed.append(f"{num_val}. ")
            i += 1
            continue
            
        # 开头 l. 或 I.
        line = re.sub(r'^[lI]\s*[\.、．·:：\s]\s*', '1. ', line)
        # 如果是 0 开头且后面跟着汉字，通常是 C 选项被识别成 0
        if re.match(r'^0\s+[\u4e00-\u9fa5]', line):
            line = 'C. ' + line[2:].strip()
        # 开头数字但没有点，例如 "6 毛泽东同志说"
        m_nodot = re.match(r'^(\d{1,3})\s+([\u4e00-\u9fa5“\"\'《])', line)
        if m_nodot and int(m_nodot.group(1)) > 0 and m_nodot.group(2) not in ['年', '月', '日', '号', '点', '个', '条', '项', '批', '期', '卷']:
            line = f"{m_nodot.group(1)}. {m_nodot.group(2)}{line[m_nodot.end():]}"
            
        processed.append(line)
        i += 1

    # 组合全文并切分题目
    full_text = "\n" + "\n".join(processed)
    
    # 按照 \n(?=\d{1,3}\s*[\.、．·:：]) 切分
    chunks = re.split(r'\n(?=\d{1,3}\s*[\.、．·:：])', full_text)
    
    questions = []
    for c in chunks:
        c = c.strip()
        if not c: continue
        m_head = re.match(r'^(\d{1,3})\s*[\.、．·:：]\s*([\s\S]+)', c)
        if not m_head: continue
        qnum = int(m_head.group(1))
        body = m_head.group(2).strip()
        
        # 选项标准化
        def norm_opt(m):
            k = m.group(1).upper()
            if k in ['①', '1']: return '\nA. '
            if k in ['②', '2', '8', '13']: return '\nB. '
            if k in ['③', '3', '0', 'O']: return '\nC. '
            if k in ['④', '4', 'L)']: return '\nD. '
            return f'\n{k}. '

        # 匹配行首或空格后的 A. B. C. D.
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
            if len(stem) >= 5 and len(final_opts) >= 2:
                questions.append({
                    'q_num': qnum,
                    'stem': stem,
                    'options': final_opts
                })
    return questions

q_lines = get_chapter_lines('backend/1000_q_txt', 4, 6)
qs = parse_robust_questions(q_lines)
print(f"Total questions parsed: {len(qs)}")
for q in qs:
    print(f"Q{q['q_num']:02d}: opts={[o['key'] for o in q['options']]} | Stem={q['stem'][:35]}")
