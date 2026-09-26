import os
import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_text_from_range(folder, start_p, end_p):
    text = ""
    for p in range(start_p, end_p + 1):
        f = os.path.join(folder, f"page_{p:03d}.txt")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8-sig") as fp:
                text += f"\n=== Page {p} ===\n" + fp.read()
    return text

def parse_1000_explanations(exp_text):
    # 标准化
    exp_map = {}
    
    # 肖秀荣解析格式：常见形如
    # "答案 B 〖 解析 〗 本题考查..." 或 "3 . 答案 C 〖 解析 〗..." 或 "4 . D 〖 解析 〗..."
    # 让我们按题目切分
    # 模式：行首数字 + 点 + 答案 / 行首 答案
    blocks = re.split(r'\n(?=(?:\d{1,3}\s*[\.、．·:：]?\s*)?(?:答\s*案|答案|[A-D]{1,4}\s*〖\s*解析))', exp_text)
    
    current_qnum = 1
    for b in blocks:
        b = b.strip()
        if not b or '解析' not in b:
            continue
        
        # 寻找题号与答案
        # 模式1: 3 . 答案 C 〖 解析 〗
        # 模式2: 答案 B 〖 解析 〗
        # 模式3: 4 二 二 」 D 〖 解析 〗
        # 模式4: 8 案 《 A 〖 解析 〗
        m_ans = re.search(r'(?:(\d{1,3})\s*[\.、．·:：\s]*)?(?:答\s*案|答案|爷\s*案|案|」)\s*[:：\(<〖\s]*([A-Da-d]{1,4})[\)\]>〗\s]*(?:〖?\s*解析\s*〗?)([\s\S]*)', b)
        if not m_ans:
            # 备用模式：直接 [A-D] 〖 解析 〗
            m_ans = re.search(r'(?:(\d{1,3})\s*[\.、．·:：\s]*)?([A-Da-d]{1,4})\s*〖\s*解析\s*〗([\s\S]*)', b)
            
        if m_ans:
            q_num_str = m_ans.group(1)
            ans = m_ans.group(2).upper()
            exp_content = m_ans.group(3).strip()
            
            if q_num_str:
                q_num = int(q_num_str)
            else:
                q_num = current_qnum
                
            clean_exp = re.sub(r'=== Page \d+ ===', '', exp_content)
            clean_exp = re.sub(r'[\s\n]+', ' ', clean_exp).strip()
            exp_map[q_num] = {
                "answer": ans,
                "explanation": f"【肖秀荣1000题名师精解】{clean_exp}"
            }
            current_qnum = q_num + 1

    return exp_map

def parse_1000_questions(q_text):
    # 试题切分
    pattern = re.compile(r'\n(?=\s*(\d{1,3})\s*[\.、．·:：]\s*(?:[\u4e00-\u9fa5“\"\'《A-Za-z]|\d{1,4}))')
    chunks = pattern.split("\n" + q_text)
    
    questions = []
    seen = set()
    for c in chunks:
        c = c.strip()
        if not c:
            continue
        m_num = re.match(r'^\s*(\d{1,3})\s*[\.、．·:：]\s*([\s\S]+)', c)
        if not m_num:
            continue
        q_num = int(m_num.group(1))
        if q_num in seen:
            continue
        body = m_num.group(2).strip()

        # 选项标准化
        def normalize_opt_key(m):
            k = m.group(1).replace('(', '').replace(')', '').strip().upper()
            if k in ['①', '1', 'A']: return '\nA. '
            if k in ['②', '2', '8', '13', 'B']: return '\nB. '
            if k in ['③', '3', '0', 'O', 'C']: return '\nC. '
            if k in ['④', '4', 'L)', 'D']: return '\nD. '
            return f'\n{k}. '

        body = re.sub(r'(?:^|\s+)([A-Da-d①②③④80oO]|L\)|13|\([A-Da-d]\))\s*[\.、．，,·:：\s]\s*', normalize_opt_key, body)
        opt_pattern = re.compile(r'\n([A-D])\.\s*([\s\S]*?)(?=(?:\n[A-D]\.)|\Z)')
        opt_matches = list(opt_pattern.finditer(body))

        if len(opt_matches) >= 2:
            stem = body[:opt_matches[0].start()].strip()
            stem = re.sub(r'=== Page \d+ ===', '', stem)
            stem = re.sub(r'[\s\n]+', ' ', stem).strip()
            stem = re.sub(r'^\d{1,3}\s*[\.、．·:：]\s*', '', stem)

            opts = {}
            for om in opt_matches:
                k = om.group(1).upper()
                v = om.group(2).strip()
                v = re.sub(r'^[A-Da-d①②③④\(\)]\s*[\.、．，,·:\s]\s*', '', v)
                v = re.sub(r'\s*\d{1,3}\s*[\.、．·:：]\s*[\u4e00-\u9fa5“\"\'《].*$', '', v)
                v = re.sub(r'=== Page \d+ ===[\s\S]*$', '', v)
                v = re.sub(r'[\s\n]+', ' ', v).strip()
                if k in ['A', 'B', 'C', 'D'] and v:
                    opts[k] = v

            final_opts = []
            for k in ['A', 'B', 'C', 'D']:
                if k in opts:
                    final_opts.append({'key': k, 'value': opts[k]})

            if len(stem) >= 6 and len(final_opts) >= 2:
                questions.append({
                    "q_num": q_num,
                    "stem": stem,
                    "options": final_opts
                })
                seen.add(q_num)

    return sorted(questions, key=lambda x: x["q_num"])

if __name__ == '__main__':
    q_txt = get_text_from_range('backend/1000_q_txt', 4, 6)
    exp_txt = get_text_from_range('backend/1000_exp_txt', 3, 5)

    qs = parse_1000_questions(q_txt)
    exps = parse_1000_explanations(exp_txt)

    print(f"Parsed {len(qs)} questions from Q pages 4..6")
    print(f"Parsed {len(exps)} explanations from Exp pages 3..5")
    for q in qs:
        num = q['q_num']
        has_exp = num in exps
        ans = exps[num]['answer'] if has_exp else 'MISSING'
        exp_prev = exps[num]['explanation'][:50] if has_exp else ''
        print(f"Q{num}: Ans={ans:4s} | Stem: {q['stem'][:35]} | Exp: {exp_prev}")
