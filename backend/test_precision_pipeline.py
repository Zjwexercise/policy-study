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
            lines.append(l_s)

    pattern = re.compile(
        r'(?:(?:^|[\s\n])(\d{1,3})\s*[\.、．·:：•\s]*)?'
        r'(?:答案|爷案|答索|答对|爷搴|案|〕)?\s*'
        r'(?:[\(\[<《\s]*([A-Da-d801]{1,4})[\)\]>》\s]*)?'
        r'[〖（\[(【]解析[〗）\])】]?'
    )

    starts = []
    for i, line in enumerate(lines):
        # 必须包含解析二字
        if not re.search(r'[〖（\[(【]解析|解析[〗）\])】]', line):
            continue
        m = pattern.search(line)
        if m:
            qnum_str = m.group(1)
            ans = m.group(2).upper() if m.group(2) else ""
            ans_clean = ""
            for ch in ans:
                if ch == '8': ans_clean += 'B'
                elif ch == '0': ans_clean += 'C'
                elif ch == '1': ans_clean += 'A'
                elif ch in 'ABCD': ans_clean += ch
                
            if not qnum_str and i > 0:
                m_prev = re.match(r'^(\d{1,3})\s*[\.、．·:：]?$', lines[i-1])
                if m_prev:
                    qnum_str = m_prev.group(1)
            starts.append((i, int(qnum_str) if qnum_str else None, ans_clean, line))

    exp_items = []
    for idx, (start_idx, qnum, ans, line) in enumerate(starts):
        end_idx = starts[idx+1][0] if idx+1 < len(starts) else len(lines)
        chunk_lines = lines[start_idx:end_idx]
        full_chunk = " ".join(chunk_lines)
        body = pattern.sub('', full_chunk, count=1).strip()
        body = re.sub(r'^[〖（\[(【]解析[〗）\])】]?\s*', '', body).strip()
        body = re.sub(r'[\s\n]+', ' ', body).strip()
        
        # 如果题头没有答案，或者在正文中有明确结论：
        m_concl = re.search(r'(?:应选|故选|故应选|正确(?:选项|答案)是?)\s*([A-D](?:[、\s,与和]+[A-D])*)\s*(?:两|三|四)?项?|([A-D])\s*项正确', body)
        if m_concl:
            concl_str = m_concl.group(1) or m_concl.group(2)
            concl_ans = "".join(re.findall(r'[A-D]', concl_str))
            if concl_ans and (not ans or concl_ans != ans):
                ans = concl_ans

        exp_items.append({
            'index': idx + 1,
            'qnum': qnum,
            'answer': ans,
            'explanation': f"【肖秀荣1000题精解】{body}"
        })
    return exp_items

def parse_chapter_questions(folder, start_p, end_p, chapter_title=""):
    all_lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        raw_lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        # 移除前几行的页眉
        start_idx = 0
        while start_idx < min(4, len(raw_lines)):
            l = raw_lines[start_idx]
            if re.search(r'考研政治精雕细刻|第[一二三四五]部分|第[一二三四五六七八九十\d]+章|导论|世界的物质性|^[一二三四]、[单多]项选择题$|^[总一早]$', l):
                start_idx += 1
            else:
                break
                
        # 移除页尾页码
        end_idx = len(raw_lines)
        if end_idx > start_idx and re.match(r'^\d{1,3}$', raw_lines[-1]):
            end_idx -= 1
            
        all_lines.extend(raw_lines[start_idx:end_idx])

    # 处理倒置
    fixed_lines = []
    i = 0
    while i < len(all_lines):
        line = all_lines[i]
        
        # 过滤插入在选项中间的“项选择题”或“二、多项选择题”
        if re.search(r'^[单多]?项选择题$|^[一二三四]、[单多]项选择题$', line):
            i += 1
            continue
            
        # standalone 选项字母
        m_opt_stand = re.match(r'^([A-Da-d])\s*[\.、．·:：]?$', line)
        if m_opt_stand and fixed_lines:
            k = m_opt_stand.group(1).upper()
            prev = fixed_lines.pop()
            fixed_lines.append(f"{k}. {prev}")
            i += 1
            continue
            
        # standalone 题号
        m_num_stand = re.match(r'^([lI\]\d]{1,3})\s*[\.、．·:：]?$', line)
        if m_num_stand and fixed_lines:
            num_str = m_num_stand.group(1).replace('l', '1').replace('I', '1').replace(']', '1')
            prev = fixed_lines.pop()
            if not re.match(r'^[A-Da-d①②③④80oO]\s*[\.、．·:：\s]', prev) and not re.match(r'^[（\(]\s*[。·\.]', prev):
                fixed_lines.append(f"{num_str}. {prev}")
            else:
                fixed_lines.append(prev)
                fixed_lines.append(f"{num_str}. ")
            i += 1
            continue
            
        fixed_lines.append(line)
        i += 1

    # 选项规范化
    def norm_opt_line(l):
        m = re.match(r'^(?:[（\(]\s*[。·\.]|([A-Da-d①②③④80oO]|L\)|13))\s*[\.、．·:：，,\s]\s*([\s\S]*)', l)
        if m:
            k_raw = m.group(1)
            rest = m.group(2)
            if not k_raw: return 'C', rest
            k = k_raw.upper()
            if k in ['A', '①', '1']: return 'A', rest
            if k in ['B', '②', '2', '8', '13']: return 'B', rest
            if k in ['C', '③', '3', '0', 'O']: return 'C', rest
            if k in ['D', '④', '4', 'L)']: return 'D', rest
        return None, l

    # 显式题号
    def get_explicit_qnum(l, expected_num):
        l_fixed = re.sub(r'^\]\s*(\d)', r'1\1', l)
        l_fixed = re.sub(r'^(\d)\s*&', r'\g<1>8', l_fixed)
        m = re.match(r'^([lI\d]{1,3})\s*[\.、．·:：，,\s]\s*([\u4e00-\u9fa5“\"\'《])', l_fixed)
        if m:
            first_ch = m.group(2)
            if first_ch in ['年', '月', '日', '号', '点', '个', '条', '项', '批', '期', '卷', '世', '代', '分', '秒']:
                return None, l
            num_val = int(m.group(1).replace('l', '1').replace('I', '1'))
            if expected_num and expected_num >= 10 and num_val == (expected_num % 10):
                num_val = expected_num
            if num_val > 0:
                rest = l_fixed[m.end(1):].lstrip(' .、．·:：，,')
                return num_val, rest
        return None, l

    questions = []
    current_stem_lines = []
    current_opts = {}
    current_qnum = None
    expected_qnum = 1
    
    def finish_current_question():
        nonlocal current_stem_lines, current_opts, current_qnum, expected_qnum
        if current_stem_lines and len(current_opts) >= 2:
            stem = " ".join(current_stem_lines).strip()
            stem = re.sub(r'^\d{1,3}\s*[\.、．·:：，,]\s*', '', stem)
            
            final_opts = []
            for k in ['A', 'B', 'C', 'D']:
                if k in current_opts:
                    final_opts.append({'key': k, 'value': current_opts[k]})
                    
            qnum_final = current_qnum if current_qnum else expected_qnum
            questions.append({
                'qnum': qnum_final,
                'stem': stem,
                'options': final_opts
            })
            expected_qnum = qnum_final + 1
        current_stem_lines = []
        current_opts = {}
        current_qnum = None

    idx = 0
    while idx < len(fixed_lines):
        line = fixed_lines[idx]
        opt_key, opt_val = norm_opt_line(line)
        
        if opt_key:
            current_opts[opt_key] = opt_val.strip()
            idx += 1
            continue
            
        # 检查是否是由于漏了选项字母而产生的中间行 (例如有 A，当前行无字母，但下一行是 C)
        if current_opts and 'A' in current_opts and 'B' not in current_opts and idx + 1 < len(fixed_lines):
            next_key, _ = norm_opt_line(fixed_lines[idx+1])
            if next_key in ['C', 'D']:
                current_opts['B'] = line.strip()
                idx += 1
                continue
                
        if current_opts and 'B' in current_opts and 'C' not in current_opts and idx + 1 < len(fixed_lines):
            next_key, _ = norm_opt_line(fixed_lines[idx+1])
            if next_key == 'D':
                current_opts['C'] = line.strip()
                idx += 1
                continue
            
        qnum_found, rest_text = get_explicit_qnum(line, expected_qnum)
        if qnum_found:
            finish_current_question()
            current_qnum = qnum_found
            current_stem_lines.append(rest_text)
            idx += 1
            continue
            
        if current_opts:
            finish_current_question()
            current_stem_lines.append(line)
        else:
            current_stem_lines.append(line)
        idx += 1

    finish_current_question()
    return questions

# 测试 Ch1
ch1_exps = parse_chapter_explanations('backend/1000_exp_txt', 3, 5) # Ch1 is pages 3..5
ch1_qs = parse_chapter_questions('backend/1000_q_txt', 4, 6)
print(f"Ch1: Q={len(ch1_qs)}, Exp={len(ch1_exps)}")
for i in range(min(len(ch1_qs), len(ch1_exps))):
    q = ch1_qs[i]
    e = ch1_exps[i]
    print(f"Q{i+1:2d} (Qnum={q['qnum']:2d}): Ans={e['answer']:4s} | Opts={[o['key'] for o in q['options']]} | Stem={q['stem'][:25]} | Exp={e['explanation'][:35]}")

print("\n" + "="*50 + "\n")

# 测试 Ch2
ch2_exps = parse_chapter_explanations('backend/1000_exp_txt', 6, 17) # Ch2 is pages 6..17 (first 3 were Ch1, so 40 items)
# 排除前面的 Ch1 遗留
ch2_exps = [e for e in ch2_exps if '长征精神' in e['explanation'] or e['index'] >= 4]
ch2_qs = parse_chapter_questions('backend/1000_q_txt', 7, 16)
print(f"Ch2: Q={len(ch2_qs)}, Exp={len(ch2_exps)}")
for i in range(min(len(ch2_qs), len(ch2_exps))):
    q = ch2_qs[i]
    e = ch2_exps[i]
    print(f"Q{i+1:2d} (Qnum={q['qnum']:2d}): Ans={e['answer']:4s} | Opts={[o['key'] for o in q['options']]} | Stem={q['stem'][:25]} | Exp={e['explanation'][:35]}")
