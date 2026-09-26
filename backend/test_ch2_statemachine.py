import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

from test_ch2_stitch import lines

def parse_questions_state_machine(lines):
    # 第一步：先处理行倒置 (standalone 题号如 "5 ．")
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m_stand = re.match(r'^([lI\d]{1,3})\s*[\.、．·:：]?$', line)
        if m_stand and fixed_lines:
            num_str = m_stand.group(1).replace('l', '1').replace('I', '1')
            prev = fixed_lines.pop()
            # 如果上一行不是选项开头
            if not re.match(r'^[A-Da-d①②③④80oO]\s*[\.、．·:：\s]', prev) and not re.match(r'^[（\(]\s*[。·\.]', prev):
                # 倒置了，把上一行移到题号后面
                fixed_lines.append(f"{num_str}. {prev}")
            else:
                fixed_lines.append(prev)
                fixed_lines.append(f"{num_str}. ")
            i += 1
            continue
        fixed_lines.append(line)
        i += 1

    # 第二步：规范化选项行与显式题号
    # 选项前缀规范化函数
    def norm_opt_line(l):
        # 匹配诸如: "A 精神...", "B. 没有人脑...", "c 精神...", "0 人的实践...", "（ 。开放性", "8. 某某"
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
    def get_explicit_qnum(l):
        # 排除日期如 "20 世纪", "1818 年", "5 月"
        m = re.match(r'^([lI\d]{1,3})\s*[\.、．·:：，,\s]\s*([\u4e00-\u9fa5“\"\'《])', l)
        if m:
            first_ch = m.group(2)
            if first_ch in ['年', '月', '日', '号', '点', '个', '条', '项', '批', '期', '卷', '世', '代', '分', '秒']:
                return None, l
            num_val = int(m.group(1).replace('l', '1').replace('I', '1'))
            if num_val > 0:
                rest = l[m.end(1):].lstrip(' .、．·:：，,')
                return num_val, rest
        return None, l

    # 第三步：状态机抽取题目
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
        
        # 如果是选项行
        if opt_key:
            current_opts[opt_key] = opt_val.strip()
            continue
            
        # 如果不是选项行，检查是否是新题号
        qnum_found, rest_text = get_explicit_qnum(line)
        if qnum_found:
            # 结题上一道
            finish_current_question()
            current_qnum = qnum_found
            current_stem_lines.append(rest_text)
            continue
            
        # 如果既不是选项，又没有显式题号
        # 检查当前是否已经收集到了选项（即已经进入选项阶段后，突然出现非选项文本）
        if current_opts:
            # 说明上一题已经结束，当前行是下一道无显式题号的题目的题干起始！
            finish_current_question()
            current_stem_lines.append(line)
        else:
            # 仍在当前题干中
            current_stem_lines.append(line)

    finish_current_question()
    return questions

qs = parse_questions_state_machine(lines)
print(f"Total Questions parsed in Ch2: {len(qs)}")
for q in qs:
    print(f"Q{q['qnum']:02d}: opts={[o['key'] for o in q['options']]} | Stem: {q['stem'][:35]}")
