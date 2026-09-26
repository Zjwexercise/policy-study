import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

from test_ch2_stitch import lines

def parse_questions_refined(lines):
    # 第一步：处理行倒置 (standalone 题号或选项字母)
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 处理 standalone 选项字母如 "B." 或 "C." 或 "B"
        m_opt_stand = re.match(r'^([A-Da-d])\s*[\.、．·:：]?$', line)
        if m_opt_stand and fixed_lines:
            k = m_opt_stand.group(1).upper()
            prev = fixed_lines.pop()
            fixed_lines.append(f"{k}. {prev}")
            i += 1
            continue
            
        # 处理 standalone 题号如 "5 ．" 或 "4 ．"
        m_num_stand = re.match(r'^([lI\]\d]{1,3})\s*[\.、．·:：]?$', line)
        if m_num_stand and fixed_lines:
            num_str = m_num_stand.group(1).replace('l', '1').replace('I', '1').replace(']', '1')
            prev = fixed_lines.pop()
            # 如果上一行不是选项开头
            if not re.match(r'^[A-Da-d①②③④80oO]\s*[\.、．·:：\s]', prev) and not re.match(r'^[（\(]\s*[。·\.]', prev):
                fixed_lines.append(f"{num_str}. {prev}")
            else:
                fixed_lines.append(prev)
                fixed_lines.append(f"{num_str}. ")
            i += 1
            continue
            
        fixed_lines.append(line)
        i += 1

    # 规范化选项行函数
    def norm_opt_line(l):
        # 匹配各种奇葩 OCR 选项头:
        # A. / B. / C. / D. / A / B / c / d / 0 / 8 / （。 / (A) / ① / ②
        m = re.match(r'^(?:[（\(]\s*[。·\.]|([A-Da-d①②③④80oO]|L\)|13))\s*[\.、．·:：，,\s]\s*([\s\S]*)', l)
        if m:
            k_raw = m.group(1)
            rest = m.group(2)
            if not k_raw: # 是 （。
                return 'C', rest
            k = k_raw.upper()
            if k in ['A', '①', '1']: return 'A', rest
            if k in ['B', '②', '2', '8', '13']: return 'B', rest
            if k in ['C', '③', '3', '0', 'O']: return 'C', rest
            if k in ['D', '④', '4', 'L)']: return 'D', rest
        return None, l

    # 显式题号判断
    def get_explicit_qnum(l, expected_num):
        # 处理常见 OCR 题号失真: "] 5" -> "15", "1 &" -> "18", "2 &" -> "28", "3 &" -> "38"
        l_fixed = re.sub(r'^\]\s*(\d)', r'1\1', l)
        l_fixed = re.sub(r'^(\d)\s*&', r'\g<1>8', l_fixed)
        
        m = re.match(r'^([lI\d]{1,3})\s*[\.、．·:：，,\s]\s*([\u4e00-\u9fa5“\"\'《])', l_fixed)
        if m:
            first_ch = m.group(2)
            if first_ch in ['年', '月', '日', '号', '点', '个', '条', '项', '批', '期', '卷', '世', '代', '分', '秒']:
                return None, l
            num_val = int(m.group(1).replace('l', '1').replace('I', '1'))
            # 如果期望是 17，遇到 7，很可能是 17 的 1 丢了
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
            # 过滤多余题号
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

    for line in fixed_lines:
        opt_key, opt_val = norm_opt_line(line)
        
        if opt_key:
            current_opts[opt_key] = opt_val.strip()
            continue
            
        qnum_found, rest_text = get_explicit_qnum(line, expected_qnum)
        if qnum_found:
            finish_current_question()
            current_qnum = qnum_found
            current_stem_lines.append(rest_text)
            continue
            
        if current_opts:
            finish_current_question()
            current_stem_lines.append(line)
        else:
            current_stem_lines.append(line)

    finish_current_question()
    return questions

qs = parse_questions_refined(lines)
print(f"Total Questions parsed in Ch2: {len(qs)}")
for q in qs:
    print(f"Q{q['qnum']:02d}: opts={[o['key'] for o in q['options']]} | Stem: {q['stem'][:35]}")
