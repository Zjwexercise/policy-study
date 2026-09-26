import os
import sys
import re

sys.path.append(os.path.join(os.path.dirname(__file__)))
from rebuild_wb6 import TEST_SPECS, clean_ocr_text, TXT_DIR

def extract_questions_improved(text):
    # 标准化标点符号：把各种点号如 ．·、 统一或匹配
    # 题号：支持 1..30 后接标点或空格，接汉字、引号、书名号、英文或年份数字
    pattern = re.compile(r'\n(?=\s*\d{1,2}\s*[\.、．·]\s*(?:[\u4e00-\u9fa5“\"\'《A-Za-z]|\d{1,4}\s*年))')
    chunks = pattern.split('\n' + text)
    questions = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        m_num = re.match(r'^\s*(\d{1,2})\s*[\.、．·]\s*([\s\S]+)', chunk)
        if not m_num:
            continue
        q_num = int(m_num.group(1))
        if q_num < 1 or q_num > 30:
            continue
        body = m_num.group(2).strip()

        # 选项
        body = re.sub(r'(?:^|\s+)([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\s*[\.、．，,·:\s]\s*', r'\n\1. ', body)
        opt_pattern = re.compile(r'\n([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\.\s*([\s\S]*?)(?=(?:\n[A-Da-dＡ-Ｄａ-ｄ①②③④]\.)|\Z)')
        opt_matches = list(opt_pattern.finditer(body))
        if len(opt_matches) >= 2:
            stem = body[:opt_matches[0].start()].strip()
            stem = re.sub(r'[\s\n]+', ' ', stem).strip()
            stem = re.sub(r'^\d{1,2}\s*[\.、．·]\s*', '', stem)

            opts = {}
            for om in opt_matches:
                k = om.group(1).upper()
                if k in ['①', '1']: k = 'A'
                elif k in ['②', '2']: k = 'B'
                elif k in ['③', '3']: k = 'C'
                elif k in ['④', '4']: k = 'D'
                k = k.replace('(', '').replace(')', '').strip()
                if k in ['Ａ']: k = 'A'
                elif k in ['Ｂ']: k = 'B'
                elif k in ['Ｃ']: k = 'C'
                elif k in ['Ｄ']: k = 'D'
                v = om.group(2).strip()
                v = re.sub(r'[\s\n]+', ' ', v).strip()
                v = re.sub(r'\s*\d{1,2}\s*[\.、．·]\s*[\u4e00-\u9fa5“\"\'《].*$', '', v).strip()
                if k in ['A', 'B', 'C', 'D'] and v:
                    opts[k] = v
            final_opts = []
            for k in ['A', 'B', 'C', 'D']:
                if k in opts:
                    final_opts.append({'key': k, 'value': opts[k]})
            if len(stem) >= 6 and len(final_opts) >= 2:
                questions.append({'q_num': q_num, 'stem': stem, 'options': final_opts})
    return questions

def run():
    spec = [s for s in TEST_SPECS if s['category'] == '史纲' and s['test_name'] == '综合测试一'][0]
    lines = []
    for p in range(spec['q_start'], spec['q_end'] + 1):
        txt_path = os.path.join(TXT_DIR, f'page_{p:03d}.txt')
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines.extend(f.readlines())

    cleaned = clean_ocr_text(lines)
    qs = extract_questions_improved(cleaned)
    found = sorted([q['q_num'] for q in qs])
    print(f"史纲 综合测试一 Found: {len(found)}/30 -> {found}")

if __name__ == '__main__':
    run()
