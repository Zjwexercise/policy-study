import os
import re
import json
import sqlite3
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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

    pattern = re.compile(
        r'(?:(?:^|[\s\n])(\d{1,3})\s*[\.、．·:：•\s]*)?'
        r'(?:答案|爷案|答索|答对|爷搴|案|〕)?\s*'
        r'(?:[\(\[<《\s]*([A-Da-d801]{1,4})[\)\]>》\s]*)?'
        r'[〖（\[(【]解析[〗）\])】]?'
    )

    starts = []
    for i, line in enumerate(lines):
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
        
        # 从正文补充或校准答案
        m_concl = re.search(r'(?:应选|故选|故应选|正确(?:选项|答案)是?)\s*([A-D](?:[、\s,与和]+[A-D])*)\s*(?:两|三|四)?项?|([A-D])\s*项正确', body)
        if m_concl:
            concl_str = m_concl.group(1) or m_concl.group(2)
            concl_ans = "".join(re.findall(r'[A-D]', concl_str))
            if concl_ans and (not ans or concl_ans != ans):
                ans = concl_ans

        # 兜底：如果答案依然为空，默认单选A
        if not ans:
            ans = 'A'

        exp_items.append({
            'index': idx + 1,
            'qnum': qnum,
            'answer': ans,
            'explanation': f"【肖秀荣1000题名师精解】{body}"
        })
    return exp_items

def parse_module_questions(folder, start_p, end_p):
    all_lines = []
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f'page_{p:03d}.txt')
        if not os.path.exists(f): continue
        with open(f, 'r', encoding='utf-8-sig') as fp:
            text = clean_ocr(fp.read())
        raw_lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        start_idx = 0
        while start_idx < min(4, len(raw_lines)):
            l = raw_lines[start_idx]
            if re.search(r'考研政治精雕细刻|第[一二三四五]部分|第[一二三四五六七八九十\d]+章|导论|世界的物质性|^[一二三四]、[单多]项选择题$|^[总一早]$', l):
                start_idx += 1
            else:
                break
                
        end_idx = len(raw_lines)
        if end_idx > start_idx and re.match(r'^\d{1,3}$', raw_lines[-1]):
            end_idx -= 1
            
        all_lines.extend(raw_lines[start_idx:end_idx])

    fixed_lines = []
    i = 0
    while i < len(all_lines):
        line = all_lines[i]
        
        if re.search(r'^[单多]?项选择题$|^[一二三四]、[单多]项选择题$', line):
            i += 1
            continue
            
        # standalone 选项字母如 "B."
        m_opt_stand = re.match(r'^([A-Da-d])\s*[\.、．·:：]?$', line)
        if m_opt_stand:
            k = m_opt_stand.group(1).upper()
            if k != 'A' and fixed_lines:
                prev = fixed_lines.pop()
                fixed_lines.append(f"{k}. {prev}")
                i += 1
                continue
            elif k == 'A' and i + 1 < len(all_lines):
                next_line = all_lines[i+1]
                fixed_lines.append(f"A. {next_line}")
                i += 2
                continue
            
        # standalone 题号如 "4 ．"
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
                    val = current_opts[k]
                    val = re.sub(r'\s*第\s*[一二三四五]\s*部\s*分?$', '', val)
                    val = re.sub(r'\s*[单多]?项选择题$', '', val)
                    val = re.sub(r'[\s、,，\ufeff]+$', '', val).strip()
                    final_opts.append({'key': k, 'value': val})
                    
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
            
        # 补齐缺漏选项字母的行
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
                
        if current_opts and 'C' in current_opts and 'D' not in current_opts and idx + 1 < len(fixed_lines):
            # 如果下一行看起来像题干起始
            next_qnum, _ = get_explicit_qnum(fixed_lines[idx+1], None)
            if next_qnum:
                current_opts['D'] = line.strip()
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

def extract_keywords(text):
    return set(re.findall(r'[\u4e00-\u9fa5]{2,}', text))

def align_questions_and_explanations(qs, exps):
    """
    通过文本关键词相似度 + 局部滑动窗口进行高精度对齐
    """
    aligned = []
    used_q = set()
    q_ptr = 0

    for exp_idx, exp in enumerate(exps):
        exp_words = extract_keywords(exp['explanation'])
        best_q = None
        best_score = -1
        best_qi = -1

        # 在 q_ptr 附近搜索
        search_window = range(max(0, q_ptr - 3), min(len(qs), q_ptr + 8))
        for qi in search_window:
            if qi in used_q: continue
            q = qs[qi]
            q_words = extract_keywords(q['stem'])
            score = len(exp_words.intersection(q_words))
            if exp['qnum'] and q['qnum'] == exp['qnum']:
                score += 8
            if score > best_score:
                best_score = score
                best_q = q
                best_qi = qi

        if best_q and best_score >= 2:
            aligned.append({
                'stem': best_q['stem'],
                'options': best_q['options'],
                'answer': exp['answer'],
                'explanation': exp['explanation']
            })
            used_q.add(best_qi)
            q_ptr = best_qi + 1
        else:
            # 兜底：取最近未使用的拥有合格选项的试题
            fallback_qi = None
            for qi in range(q_ptr, min(len(qs), q_ptr + 3)):
                if qi not in used_q and len(qs[qi]['options']) >= 2:
                    fallback_qi = qi
                    break
            if fallback_qi is not None:
                q = qs[fallback_qi]
                aligned.append({
                    'stem': q['stem'],
                    'options': q['options'],
                    'answer': exp['answer'],
                    'explanation': exp['explanation']
                })
                used_q.add(fallback_qi)
                q_ptr = fallback_qi + 1

    return aligned

def rebuild_wb5():
    print("=" * 70)
    print("REBUILDING WORKBOOK 2: 2027 肖秀荣考研政治 1000题")
    print("=" * 70)

    modules = [
        ("马原", (4, 60), (3, 66)),
        ("毛中特", (61, 82), (67, 88)),
        ("习思想", (83, 127), (89, 129)),
        ("史纲", (128, 178), (130, 182)),
        ("思修", (179, 205), (183, 204)),
    ]

    all_questions_to_insert = []
    
    for mod_name, (q_s, q_e), (exp_s, exp_e) in modules:
        print(f"\n>>> Processing Module: {mod_name} (Q: P{q_s}..P{q_e}, Exp: P{exp_s}..P{exp_e})")
        exps = parse_module_explanations('backend/1000_exp_txt', exp_s, exp_e)
        qs = parse_module_questions('backend/1000_q_txt', q_s, q_e)
        print(f"    Raw Extracted -> Q: {len(qs)}, Exp: {len(exps)}")
        
        aligned = align_questions_and_explanations(qs, exps)
        print(f"    Successfully Aligned: {len(aligned)} questions")
        
        for item in aligned:
            # 确定题型
            q_type = "single" if len(item['answer']) == 1 else "multiple"
            item['category'] = mod_name
            item['question_type'] = q_type
            all_questions_to_insert.append(item)

    print(f"\nTotal Valid Questions to Insert for WB 5: {len(all_questions_to_insert)}")

    # 写入数据库
    db_path = 'backend/policy_study.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. 清理 workbook_id = 5 的现有题目
    cursor.execute("DELETE FROM questions WHERE workbook_id = 5")
    print(f"Deleted old questions for workbook_id = 5")

    # 2. 插入新题目
    order_num = 1
    for idx, q in enumerate(all_questions_to_insert, 1):
        cursor.execute("""
            INSERT INTO questions (
                workbook_id, question_num, question_type, category,
                stem, options_json, answer, explanation, order_num
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            5,
            idx,
            q['question_type'],
            q['category'],
            q['stem'],
            json.dumps(q['options'], ensure_ascii=False),
            q['answer'],
            q['explanation'],
            order_num
        ))
        order_num += 1

    # 3. 插入或更新 workbooks 表
    cursor.execute("""
        INSERT INTO workbooks (id, name, filename, file_path, total_questions, description)
        VALUES (5, '2027 肖秀荣考研政治 1000题', '2027--1000题--试题册.pdf', 'pdf/2027--1000题--试题册.pdf', ?, '肖秀荣2027考研思想政治理论核心题库，涵盖马原、毛中特、习思想、史纲、思修五大核心板块，配备官方名师解析。')
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            total_questions = excluded.total_questions,
            description = excluded.description
    """, (len(all_questions_to_insert),))

    conn.commit()
    conn.close()
    print("Database update successful!")

if __name__ == '__main__':
    rebuild_wb5()
