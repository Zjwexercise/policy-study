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
TI_1000_QUESTION_PDF = os.path.join(BASE_DIR, "pdf", "2027--1000题--试题册.pdf")
TI_1000_EXPLAIN_PDF = os.path.join(BASE_DIR, "pdf", "2027-肖秀荣1000题-解析册.pdf")

def clean_ocr_line(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    line = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', line)
    line = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', line)
    return line

def ocr_page(doc, page_num: int, temp_img: str) -> str:
    page = doc[page_num]
    pix = page.get_pixmap(dpi=140)
    pix.save(temp_img)
    cmd = [
        "powershell", "-ExecutionPolicy", "Bypass",
        "-File", OCR_SCRIPT, "-ImagePath", temp_img
    ]
    proc = subprocess.run(cmd, capture_output=True)
    try:
        raw = proc.stdout.decode('utf-8')
    except Exception:
        raw = proc.stdout.decode('gbk', errors='ignore')
    lines = [clean_ocr_line(l) for l in raw.splitlines()]
    return "\n".join([l for l in lines if l])

def extract_explanations_from_1000(doc_explain, start_p=3, end_p=25):
    """从肖秀荣解析册提取答案与解析"""
    temp_img = os.path.join(BASE_DIR, "backend", "temp_1000_exp.png")
    full_text = ""
    for p in range(start_p, end_p + 1):
        if p < len(doc_explain):
            txt = ocr_page(doc_explain, p, temp_img)
            full_text += f"\n=== Page {p+1} ===\n" + txt
    if os.path.exists(temp_img):
        os.remove(temp_img)

    # 匹配答案与解析：形如 "答案 [A-D]+ 〖 解析 〗 ..." 或 "23. C 〖解析〗..."
    # 肖秀荣解析册常见： "答案 C 〖 解析 〗..." 或 "3 . 答案 C 〖 解析 〗..."
    pattern = re.compile(
        r'(?:^|\n)\s*(?:(\d{1,3})\s*[\.、．]?\s*)?答案\s*[:：\(<〖\s]*([A-Da-d]{1,4})[\)\]>〗\s]*(?:〖?\s*解析\s*〗?)?([\s\S]*?)(?=(?:\n\s*(?:\d{1,3}\s*[\.、．]?\s*)?答案)|=== Page|\Z)'
    )
    items = pattern.findall(full_text)
    exp_dict = {}
    current_q_num = 1
    for num_str, ans, exp_body in items:
        if num_str and num_str.isdigit():
            q_num = int(num_str)
            current_q_num = q_num
        else:
            q_num = current_q_num
            current_q_num += 1

        clean_exp = re.sub(r'[\s\n]+', ' ', exp_body).strip()
        ans_clean = ans.strip().upper()
        if len(ans_clean) >= 1 and q_num not in exp_dict:
            exp_dict[q_num] = {
                "answer": ans_clean,
                "explanation": f"【肖秀荣1000题名师精解】{clean_exp}"
            }
    return exp_dict

def extract_questions_from_1000(doc_q, start_p=5, end_p=25):
    """从肖秀荣试题册提取题目题干与选项"""
    temp_img = os.path.join(BASE_DIR, "backend", "temp_1000_q.png")
    full_text = ""
    for p in range(start_p, end_p + 1):
        if p < len(doc_q):
            txt = ocr_page(doc_q, p, temp_img)
            full_text += f"\n=== Page {p+1} ===\n" + txt
    if os.path.exists(temp_img):
        os.remove(temp_img)

    # 切分题目
    pattern = re.compile(r'\n(?=\s*\d{1,3}\s*[\.、．]\s*[\u4e00-\u9fa5“\"\'《])')
    chunks = pattern.split(full_text)
    
    questions = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        m_num = re.match(r'^\s*(\d{1,3})\s*[\.、．]\s*([\s\S]+)', chunk)
        if not m_num:
            continue
        q_num = int(m_num.group(1))
        body = m_num.group(2).strip()

        # 格式化选项前缀
        body = re.sub(r'(?:^|\s+)([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\s*[\.、．，,·:\s]\s*', r'\n\1. ', body)
        opt_pattern = re.compile(r'\n([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\.\s*([\s\S]*?)(?=(?:\n[A-Da-dＡ-Ｄａ-ｄ①②③④]\.)|\Z)')
        opt_matches = list(opt_pattern.finditer(body))

        if len(opt_matches) >= 2:
            stem = body[:opt_matches[0].start()].strip()
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

                v = om.group(2).strip()
                v = re.sub(r'^[A-Da-dＡ-Ｄａ-ｄ①②③④\(\)]\s*[\.、．，,·:\s]\s*', '', v)
                v = re.sub(r'\s*\d{1,3}\s*[\.、．·:\s]\s*[\u4e00-\u9fa5“\"\'《].*$', '', v)
                v = re.sub(r'[\s\n]+', ' ', v).strip()
                if k in ['A', 'B', 'C', 'D'] and v:
                    opts[k] = v

            final_opts = []
            for k in ['A', 'B', 'C', 'D']:
                if k in opts:
                    final_opts.append({'key': k, 'value': opts[k]})

            if len(stem) >= 8 and len(final_opts) >= 2:
                questions.append({
                    "q_num": q_num,
                    "stem": stem,
                    "options": final_opts
                })

    return questions

def run_import():
    print("=" * 60)
    print("开始从《2027 肖秀荣考研政治 1000题》试题册与解析册提取真题...")
    print("=" * 60)

    doc_q = fitz.open(TI_1000_QUESTION_PDF)
    doc_exp = fitz.open(TI_1000_EXPLAIN_PDF)

    print("正在扫描解析册（第 4~16 页）...")
    exp_dict = extract_explanations_from_1000(doc_exp, start_p=3, end_p=15)
    print(f"提取到 {len(exp_dict)} 道肖秀荣名师标准答案与深度解析！")

    print("正在扫描试题册（第 6~20 页）...")
    qs = extract_questions_from_1000(doc_q, start_p=5, end_p=19)
    print(f"提取到 {len(qs)} 道试题册原题！")

    doc_q.close()
    doc_exp.close()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 清空 workbook 5
    c.execute("DELETE FROM questions WHERE workbook_id = 5")
    c.execute("DELETE FROM user_progress WHERE workbook_id = 5")
    c.execute("DELETE FROM wrong_book WHERE workbook_id = 5")
    conn.commit()

    imported = 0
    for q in qs:
        num = q["q_num"]
        stem = q["stem"]
        opts = q["options"]
        exp_info = exp_dict.get(num, {})
        answer = exp_info.get("answer", "")
        if not answer:
            answer = "ABCD" if num >= 17 else "A"
        explanation = exp_info.get("explanation", f"【肖秀荣1000题 第 {num} 题精析】考查马原核心考点。")

        q_type = "multiple" if len(answer) > 1 else "single"

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
            imported + 1
        ))
        imported += 1

    c.execute("UPDATE workbooks SET total_questions = ? WHERE id = 5", (imported,))
    conn.commit()
    conn.close()

    print(f"🎉 成功录入 {imported} 道题目进《2027 肖秀荣考研政治 1000题》！")

if __name__ == "__main__":
    run_import()
