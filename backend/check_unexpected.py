import os
import sys
import fitz

sys.path.append(os.path.join(os.path.dirname(__file__)))
from rebuild_wb6 import TEST_SPECS, clean_ocr_text, extract_questions_from_text, parse_test_explanations, TXT_DIR, YOUTIKU_EXPLAIN_PDF

doc_exp = fitz.open(YOUTIKU_EXPLAIN_PDF)
for spec in TEST_SPECS:
    cat = spec['category']
    tname = spec['test_name']
    exp_dict = parse_test_explanations(doc_exp, spec['exp_start'], spec['exp_end'])
    test_lines = []
    for p in range(spec['q_start'], spec['q_end'] + 1):
        txt_path = os.path.join(TXT_DIR, f'page_{p:03d}.txt')
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                test_lines.extend(f.readlines())
    cleaned = clean_ocr_text(test_lines)
    qs = extract_questions_from_text(cleaned)
    for q in qs:
        num = q['q_num']
        if num not in exp_dict:
            stem_prev = q['stem'][:40]
            print(f"[{cat} {tname}] Unexpected Q num: {num} | Stem: {stem_prev}")
