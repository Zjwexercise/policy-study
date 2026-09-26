import sys
import io
import json
import re
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Strict teacher commentary keywords in options
COMMENTARY_KEYWORDS = [
    '表述正确', '表述错误', '对应错误', '对应镨误', '对应正确',
    '不合题意', '不符合题意', '常见干扰项', '常见十挽项', '干扰项设置',
    '绝对表述', '绝对表达', '第一梯队', '完成时态', '时态 K', '老研政治',
    '说法错误', '说法正确', '说反了', '尚未完全掌握'
]

COMMENTARY_PATTERN = re.compile(
    r'[\s，,。；;、]*(' + '|'.join(COMMENTARY_KEYWORDS) + r')[\s\S]*$'
)

def clean_stem(stem: str) -> str:
    if not stem:
        return ""
    # Leading/inline OCR bullet artifacts
    s = stem
    s = re.sub(r'([。？！；\s])胡\s*这表明', r'\1这表明', s)
    s = re.sub(r'([。？！；\s])目\s*这', r'\1这', s)
    s = re.sub(r'([。？！；\s])目\s*这种', r'\1这种', s)
    s = re.sub(r'([。？！；\s])日\s*这说明', r'\1这说明', s)
    s = re.sub(r'([。？！；\s])日\s*这定了', r'\1这决定了', s)
    s = re.sub(r'([。？！；\s])目\s*人们', r'\1人们', s)
    s = re.sub(r'([。？！；\s])目\s*其中', r'\1其中', s)
    s = re.sub(r'([。？！；\s])卩\s*其中', r'\1其中', s)
    s = re.sub(r'([。？！；\s])卩\s*下列', r'\1下列', s)
    s = re.sub(r'([。？！；\s])l\'\s*这是因', r'\1这是因为', s)
    s = re.sub(r'•\.\'|\s*、\s*\'', '', s)
    s = re.sub(r'说\s*明\s*马\s*（\s*）', '说明马克思主义（ ）', s)
    s = re.sub(r'目\s*艹\s*特色一塗体糸', '中国特色社会主义理论体系', s)
    s = re.sub(r'目\s*中\s*特色', '中国特色', s)
    
    # Clean leading punctuation or bullet if present
    s = re.sub(r'^[胡目日卩艹孑■▲●★\s·]+', '', s)
    
    # Clean redundant spaces around Chinese punctuation: e.g. "马克思 、 恩格斯" -> "马克思、恩格斯"
    # Do 2 passes
    for _ in range(2):
        s = re.sub(r'([\u4e00-\u9fa5“\"\'《（(])\s+([，。、：；！？）)”\"\'》])', r'\1\2', s)
        s = re.sub(r'([，。、：；！？（(《])\s+([\u4e00-\u9fa5“\"\'《（()])', r'\1\2', s)
        s = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', s)
    
    return s.strip()

def clean_explanation(exp: str) -> str:
    if not exp:
        return ""
    e = exp
    e = re.sub(r'满耨巫考@|巫考|老研政治', '', e)
    e = re.sub(r'^晰膂\s*\d*\s*', '【考点解析】', e)
    e = re.sub(r'^\s*【?\s*解析\s*】?\s*', '', e)
    e = re.sub(r'[\s\n]+', ' ', e).strip()
    return e

def process_all():
    with open('frontend/public/data/all_questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)

    cleaned_questions = []
    dropped_count = 0
    option_fixed_count = 0
    stem_fixed_count = 0

    for q in questions:
        stem = clean_stem(q.get('stem', ''))
        opts = q.get('options', [])
        ans = q.get('answer', '').strip().upper()
        exp = clean_explanation(q.get('explanation', ''))
        wbid = q.get('workbook_id')

        # Drop broken unsolvable questions in WB5
        opt_keys = [o['key'] for o in opts]
        has_invalid_ans = any(a not in opt_keys for a in ans)
        is_broken_stem = len(stem) < 8 or stem.startswith('阅读材料') or stem.startswith('材料 1') or stem.startswith('材料 2')
        is_missing_opts = len(opts) < 4

        if has_invalid_ans or is_broken_stem or is_missing_opts:
            # Drop unfixable corrupted question
            dropped_count += 1
            continue

        # Clean options and extract teacher commentary
        extracted_notes = []
        new_opts = []
        for opt in opts:
            k = opt['key']
            val = opt['value']
            
            # Strip trailing OCR noise
            val = re.sub(r'[孑艹目胡■▲●★\s]+$', '', val).strip()
            
            # Check for commentary
            m = COMMENTARY_PATTERN.search(val)
            if m:
                clean_val = val[:m.start()].strip()
                note_part = val[m.start():].strip()
                # Clean note part prefix
                note_part = re.sub(r'^[，,。；;、\s]+', '', note_part).strip()
                
                # If clean_val is empty or too short, keep original without the keyword
                if len(clean_val) >= 2:
                    val = clean_val
                    extracted_notes.append(f"选项{k}：{note_part}")
                    option_fixed_count += 1
            
            # Clean Chinese spaces in option
            for _ in range(2):
                val = re.sub(r'([\u4e00-\u9fa5“\"\'《（(])\s+([，。、：；！？）)”\"\'》])', r'\1\2', val)
                val = re.sub(r'([，。、：；！？（(《])\s+([\u4e00-\u9fa5“\"\'《（()])', r'\1\2', val)
                val = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', val)
            
            new_opts.append({'key': k, 'value': val})

        if extracted_notes:
            note_str = " 【干扰项剖析】" + "；".join(extracted_notes)
            exp = exp + note_str

        if stem != q.get('stem'):
            stem_fixed_count += 1

        cleaned_questions.append({
            **q,
            'stem': stem,
            'options': new_opts,
            'explanation': exp
        })

    print(f"Total original: {len(questions)}")
    print(f"Dropped broken questions: {dropped_count}")
    print(f"Fixed options: {option_fixed_count}")
    print(f"Fixed stems: {stem_fixed_count}")
    print(f"Total pristine questions remaining: {len(cleaned_questions)}")

    # Update workbook stats
    wb_counts = {}
    for q in cleaned_questions:
        wbid = q['workbook_id']
        wb_counts[wbid] = wb_counts.get(wbid, 0) + 1

    print("Remaining count per workbook:", wb_counts)

    # Save to all_questions.json and frontend/dist
    with open('frontend/public/data/all_questions.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_questions, f, ensure_ascii=False, indent=2)

    with open('frontend/dist/data/all_questions.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_questions, f, ensure_ascii=False, indent=2)

    # Update workbooks.json
    with open('frontend/public/data/workbooks.json', 'r', encoding='utf-8') as f:
        wbs = json.load(f)

    for wb in wbs:
        if wb['id'] in wb_counts:
            wb['total_questions'] = wb_counts[wb['id']]

    with open('frontend/public/data/workbooks.json', 'w', encoding='utf-8') as f:
        json.dump(wbs, f, ensure_ascii=False, indent=2)

    with open('frontend/dist/data/workbooks.json', 'w', encoding='utf-8') as f:
        json.dump(wbs, f, ensure_ascii=False, indent=2)

    print("Saved clean all_questions.json and workbooks.json!")

if __name__ == "__main__":
    process_all()
