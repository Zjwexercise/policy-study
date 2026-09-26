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

def parse_module_questions(folder, start_p, end_p):
    lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        for l in text.splitlines():
            l_s = l.strip()
            if not l_s: continue
            # 过滤纯页眉页脚和纯章节大标题
            if len(l_s) < 30 and re.search(r'考研政治精雕细刻|第[一二三四五]部分|第[一二三四五六七八九十\d]+章|导论|^\d{1,3}$|^[一二三四]、[单多]项选择题$', l_s):
                continue
            lines.append(l_s)

    # 1. 修复倒置题号与常见 OCR 缺陷
    processed = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 处理单独成行的题号
        m_num = re.match(r'^([lI\d]{1,3})\s*[\.、．·:：]?$', line)
        if m_num and processed:
            num_val = m_num.group(1).replace('l', '1').replace('I', '1')
            prev = processed.pop()
            if not re.match(r'^[A-Da-d①②③④80oO]\s*[\.、．·:：\s]', prev):
                # 上一行是题干的第一句话
                processed.append(f"{num_val}. {prev}")
            else:
                processed.append(prev)
                processed.append(f"{num_val}. ")
            i += 1
            continue

        # 开头 l. 或 I.
        line = re.sub(r'^[lI]\s*[\.、．·:：\s]\s*', '1. ', line)
        
        # 处理 C 选项被识别成 0、O 或 （。
        line = re.sub(r'^(?:0|O|[（\(]\s*[。·\.]?)\s*([\u4e00-\u9fa5“\"\'《])', r'C. \1', line)
        # 处理 B 选项被识别成 8
        line = re.sub(r'^8\s*[\.、．·:：\s]\s*([\u4e00-\u9fa5“\"\'《])', r'B. \1', line)
        
        # 开头数字但没有点，例如 "6 毛泽东同志说"
        m_nodot = re.match(r'^(\d{1,3})\s+([\u4e00-\u9fa5“\"\'《])', line)
        if m_nodot and int(m_nodot.group(1)) > 0 and m_nodot.group(2) not in ['年', '月', '日', '号', '点', '个', '条', '项', '批', '期', '卷']:
            line = f"{m_nodot.group(1)}. {m_nodot.group(2)}{line[m_nodot.end():]}"
            
        processed.append(line)
        i += 1

    # 2. 识别题目和选项
    # 选项标准化
    def norm_opt(m):
        k = m.group(1).upper()
        if k in ['①', '1']: return '\nA. '
        if k in ['②', '2', '8', '13']: return '\nB. '
        if k in ['③', '3', '0', 'O']: return '\nC. '
        if k in ['④', '4', 'L)']: return '\nD. '
        return f'\n{k}. '

    full_text = "\n" + "\n".join(processed)
    # 标准化选项
    full_text = re.sub(r'(?:^|\s+)([A-Da-d①②③④]|L\)|13)\s*[\.、．，,·:：\s]\s*', norm_opt, full_text)
    
    # 切分题目
    # 每个题目以 \n(\d{1,3})\. 开始
    chunks = re.split(r'\n(?=\d{1,3}\s*[\.、．·:：])', full_text)
    
    questions = []
    for c in chunks:
        c = c.strip()
        if not c: continue
        m_head = re.match(r'^(\d{1,3})\s*[\.、．·:：]\s*([\s\S]+)', c)
        if not m_head: continue
        qnum = int(m_head.group(1))
        body = m_head.group(2).strip()
        
        # 匹配选项
        opt_matches = list(re.finditer(r'\n([A-D])\.\s*([\s\S]*?)(?=(?:\n[A-D]\.)|\Z)', body))
        if len(opt_matches) >= 2:
            stem = body[:opt_matches[0].start()].strip()
            stem = re.sub(r'[\s\n]+', ' ', stem).strip()
            # 过滤掉题干前缀中的重复题号
            stem = re.sub(r'^\d{1,3}\s*[\.、．·:：]\s*', '', stem)
            
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
            if len(stem) >= 4 and len(final_opts) >= 2:
                questions.append({
                    'index': len(questions) + 1,
                    'qnum': qnum,
                    'stem': stem,
                    'options': final_opts
                })
    return questions

q_m1 = parse_module_questions('backend/1000_q_txt', 4, 60)
print(f"Total Questions parsed in M1 (马原): {len(q_m1)}")
for q in q_m1[:5]:
    print(f"#{q['index']:3d} (Q{q['qnum']:2d}): opts={[o['key'] for o in q['options']]} | Stem={q['stem'][:40]}")
print("...")
for q in q_m1[-5:]:
    print(f"#{q['index']:3d} (Q{q['qnum']:2d}): opts={[o['key'] for o in q['options']]} | Stem={q['stem'][:40]}")
