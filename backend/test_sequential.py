import os
import sys
import re
import fitz

sys.path.append(os.path.join(os.path.dirname(__file__)))
from rebuild_wb6 import TEST_SPECS, clean_ocr_text, parse_test_explanations, TXT_DIR, YOUTIKU_EXPLAIN_PDF

def parse_test_sequential(text, exp_dict):
    """
    顺序状态机解析器：严格按 1..30 顺序提取试题
    """
    lines = text.splitlines()
    questions = []
    
    # 首先预处理行：修复 OCR 常见前缀错误
    cleaned_lines = []
    for line in lines:
        l = line.strip()
        if not l:
            continue
        # 1 & -> 18.
        l = re.sub(r'^1\s*&\s*', '18. ', l)
        l = re.sub(r'^2\s*&\s*', '28. ', l)
        # 8. 如果紧随 A 之后，应为 B.
        cleaned_lines.append(l)

    # 寻找题目的起始行
    q_start_indices = {}
    current_target = 1
    
    for idx, line in enumerate(cleaned_lines):
        if current_target > 30:
            break
        # 匹配以 current_target 开头：数字 + 标点/空格
        m = re.match(r'^' + str(current_target) + r'\s*[\.、．·:：]\s*(.*)', line)
        if m:
            q_start_indices[current_target] = (idx, m.group(1))
            current_target += 1
        elif current_target in [8, 18, 28] and re.match(r'^[&日]\s*[\.、．·:：]?\s*(.*)', line):
            # 题号 8 被识为 & 或 日
            q_start_indices[current_target] = (idx, re.sub(r'^[&日]\s*[\.、．·:：]?\s*', '', line))
            current_target += 1

    # 提取每道题的完整文本块
    for num in range(1, 31):
        if num not in q_start_indices:
            continue
        start_idx, first_line_content = q_start_indices[num]
        
        # 找到下一道题的起始行
        next_nums = [n for n in range(num + 1, 32) if n in q_start_indices]
        if next_nums:
            end_idx = q_start_indices[next_nums[0]][0]
        else:
            end_idx = len(cleaned_lines)
            
        block_lines = [first_line_content] + cleaned_lines[start_idx + 1: end_idx]
        block_text = "\n".join(block_lines)

        # 规范化选项标记
        # 把行首或空格后的 A. B. C. D. 统一为标准格式
        # 修复 B 被识别为 8.，C 被识别为 0.
        block_text = re.sub(r'(?:^|\s+)([A-Da-d①②③④]|\([A-Da-d]\))\s*[\.、．，,·:\s]\s*', r'\n\1. ', block_text)
        block_text = re.sub(r'\n8\.\s*(?=[^A-D\n]*?(?:\n[CD]\.|\Z))', r'\nB. ', block_text)
        block_text = re.sub(r'\n[0oO]\.\s*(?=[^A-D\n]*?(?:\n[D]\.|\Z))', r'\nC. ', block_text)

        opt_pattern = re.compile(r'\n([A-Da-d①②③④]|\([A-Da-d]\))\.\s*([\s\S]*?)(?=(?:\n[A-Da-d①②③④]\.)|\Z)')
        opt_matches = list(opt_pattern.finditer(block_text))

        if len(opt_matches) >= 2:
            stem = block_text[:opt_matches[0].start()].strip()
            stem = re.sub(r'[\s\n]+', ' ', stem).strip()

            opts = {}
            for om in opt_matches:
                k = om.group(1).upper()
                if k in ['①', '1']: k = 'A'
                elif k in ['②', '2']: k = 'B'
                elif k in ['③', '3']: k = 'C'
                elif k in ['④', '4']: k = 'D'
                k = k.replace('(', '').replace(')', '').strip()

                v = om.group(2).strip()
                v = re.sub(r'[\s\n]+', ' ', v).strip()
                if k in ['A', 'B', 'C', 'D'] and v:
                    opts[k] = v

            final_opts = []
            for k in ['A', 'B', 'C', 'D']:
                if k in opts:
                    final_opts.append({'key': k, 'value': opts[k]})

            if len(stem) >= 6 and len(final_opts) >= 2:
                questions.append({
                    "q_num": num,
                    "stem": stem,
                    "options": final_opts
                })

    return questions

def run():
    doc_exp = fitz.open(YOUTIKU_EXPLAIN_PDF)
    total_parsed = 0
    total_matched = 0

    for spec in TEST_SPECS:
        cat = spec["category"]
        tname = spec["test_name"]
        exp_dict = parse_test_explanations(doc_exp, spec["exp_start"], spec["exp_end"])

        test_lines = []
        for p in range(spec["q_start"], spec["q_end"] + 1):
            txt_path = os.path.join(TXT_DIR, f"page_{p:03d}.txt")
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    test_lines.extend(f.readlines())

        cleaned_text = clean_ocr_text(test_lines)
        qs = parse_test_sequential(cleaned_text, exp_dict)

        q_map = {q["q_num"]: q for q in qs}
        matched = sum(1 for q_num in q_map if q_num in exp_dict)
        missing = [i for i in range(1, 31) if i not in q_map]
        print(f"[{cat} - {tname}] Found: {len(qs)}/30 | Matched: {matched}/30 | Missing: {missing}")
        total_parsed += len(qs)
        total_matched += matched

    print(f"\nTOTAL: Sequential parsed {total_parsed}/630 questions, perfectly matched {total_matched}.")
    doc_exp.close()

if __name__ == '__main__':
    run()
