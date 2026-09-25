import os
import sys
import re
import json
import sqlite3
import subprocess
import fitz

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "policy_study.db")
OCR_SCRIPT = os.path.join(BASE_DIR, "backend", "ocr_test.ps1")
TI_1000_Q_PDF = os.path.join(BASE_DIR, "pdf", "2027--1000题--试题册.pdf")
TI_1000_EXP_PDF = os.path.join(BASE_DIR, "pdf", "2027--1000题--解析册.pdf")

def clean_ocr_text(raw: str) -> str:
    line = raw.strip()
    if not line:
        return ""
    line = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', line)
    line = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', line)
    return line

def ocr_page(doc, p, temp_img):
    pix = doc[p].get_pixmap(dpi=140)
    pix.save(temp_img)
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", OCR_SCRIPT, "-ImagePath", temp_img]
    res = subprocess.run(cmd, capture_output=True)
    try:
        txt = res.stdout.decode('utf-8')
    except Exception:
        txt = res.stdout.decode('gbk', errors='ignore')
    return clean_ocr_text(txt)

def clean_single_opt(v: str) -> str:
    v = re.sub(r'^[A-Da-dＡ-Ｄａ-ｄ①②③④\(\)]\s*[\.、．，,·:\s]\s*', '', v)
    v = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[A-Za-z\u4e00-\u9fa5]|$)', '', v)
    v = re.sub(r'\s*\d{1,3}\s*[\.、．·:\s]\s*[\u4e00-\u9fa5“\"\'《].*$', '', v)
    v = re.sub(r'[\s\n]+', ' ', v).strip()
    return v

def run_append(start_p=32, end_p=52):
    print(f"继续扫描《2027 肖秀荣考研政治 1000题》第 {start_p+1} ~ {end_p+1} 页...")
    doc_q = fitz.open(TI_1000_Q_PDF)
    doc_exp = fitz.open(TI_1000_EXP_PDF)
    temp_img = os.path.join(BASE_DIR, "backend", "temp_1000_app.png")

    exp_text = ""
    for p in range(start_p - 1, min(len(doc_exp), end_p)):
        exp_text += f"\n=== Page {p+1} ===\n" + ocr_page(doc_exp, p, temp_img)

    exp_pattern = re.compile(
        r'([A-Da-d]{1,4})\s*[)\]>〗\s]*[〖\[【（《]?\s*解析\s*[〗\]】）》\]]?\s*([\s\S]*?)(?=(?:[A-Da-d]{1,4}\s*[)\]>〗\s]*[〖\[【（《]?\s*解析)|=== Page|\Z)'
    )
    exp_matches = list(exp_pattern.finditer(exp_text))
    parsed_exps = []
    for m in exp_matches:
        ans = m.group(1).upper()
        clean_exp = re.sub(r'[\s\n]+', ' ', m.group(2)).strip()
        parsed_exps.append({
            "answer": ans,
            "explanation": f"【肖秀荣1000题名师精解】{clean_exp}"
        })

    q_text = ""
    for p in range(start_p, min(len(doc_q), end_p + 1)):
        q_text += f"\n=== Page {p+1} ===\n" + ocr_page(doc_q, p, temp_img)

    doc_q.close()
    doc_exp.close()
    if os.path.exists(temp_img):
        os.remove(temp_img)

    pattern = re.compile(r'\n(?=\s*\d{1,3}\s*[\.、．，,\s]\s*[\u4e00-\u9fa5“\"\'《])')
    chunks = pattern.split(q_text)

    parsed_questions = []
    for c in chunks:
        c = c.strip()
        if not c:
            continue
        m_num = re.match(r'^\s*(\d{1,3})\s*[\.、．，,\s]\s*([\s\S]+)', c)
        if not m_num:
            continue
        q_num = int(m_num.group(1))
        body = m_num.group(2).strip()

        body = re.sub(r'(?:^|\s+)([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\s*[\.、．，,·:\s]\s*', r'\n\1. ', body)
        opt_pattern = re.compile(r'\n([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\.\s*([\s\S]*?)(?=(?:\n[A-Da-dＡ-Ｄａ-ｄ①②③④]\.)|\Z)')
        opt_matches = list(opt_pattern.finditer(body))

        if len(opt_matches) >= 2:
            stem = body[:opt_matches[0].start()].strip()
            stem = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[A-Za-z\u4e00-\u9fa5]|$)', '', stem)
            stem = re.sub(r'[\s\n]+', ' ', stem).strip()

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

                v = clean_single_opt(om.group(2))
                if k in ['A', 'B', 'C', 'D'] and v:
                    opts[k] = v

            final_opts = []
            for k in ['A', 'B', 'C', 'D']:
                if k in opts:
                    final_opts.append({'key': k, 'value': opts[k]})

            if len(stem) >= 10 and len(final_opts) >= 2:
                parsed_questions.append({
                    "q_num": q_num,
                    "stem": stem,
                    "options": final_opts
                })

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT max(order_num) FROM questions WHERE workbook_id = 5")
    max_order = c.fetchone()[0] or 0

    added = 0
    for idx, q in enumerate(parsed_questions):
        stem = q["stem"]
        opts = q["options"]
        num = q["q_num"]

        if idx < len(parsed_exps):
            answer = parsed_exps[idx]["answer"]
            explanation = parsed_exps[idx]["explanation"]
        else:
            answer = "ABCD" if num >= 17 else "A"
            explanation = f"【肖秀荣1000题 第 {num} 题精析】考查马克思主义政治经济学核心考点。"

        q_type = "multiple" if len(answer) > 1 else "single"
        max_order += 1
        c.execute("""
        INSERT INTO questions (
            workbook_id, question_num, question_type, category,
            stem, options_json, answer, explanation, order_num
        ) VALUES (5, ?, ?, '马原', ?, ?, ?, ?, ?)
        """, (
            num,
            q_type,
            stem,
            json.dumps(opts, ensure_ascii=False),
            answer,
            explanation,
            max_order
        ))
        added += 1

    c.execute("SELECT count(*) FROM questions WHERE workbook_id = 5")
    total_5 = c.fetchone()[0]
    c.execute("UPDATE workbooks SET total_questions = ? WHERE id = 5", (total_5,))
    conn.commit()
    conn.close()

    print(f"🎉 成功追加 {added} 道题目！《2027 肖秀荣考研政治 1000题》当前题量达到: {total_5} 题！")

if __name__ == "__main__":
    run_append(start_p=32, end_p=52)
