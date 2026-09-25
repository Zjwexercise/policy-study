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

def clean_ocr_line(line: str) -> str:
    """清理OCR带来的汉字间空格"""
    line = line.strip()
    if not line:
        return ""
    res = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', line)
    res = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', res)
    return res

def ocr_page_image(doc, page_num: int, temp_img: str) -> str:
    """使用 Windows 本地 OCR 识别单页 PDF 图片"""
    page = doc[page_num]
    pix = page.get_pixmap(dpi=140)
    pix.save(temp_img)

    cmd = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", OCR_SCRIPT,
        "-ImagePath", temp_img
    ]
    proc = subprocess.run(cmd, capture_output=True)
    try:
        raw = proc.stdout.decode('utf-8')
    except Exception:
        raw = proc.stdout.decode('gbk', errors='ignore')

    lines = [clean_ocr_line(l) for l in raw.splitlines()]
    return "\n".join([l for l in lines if l])

def parse_questions_from_ocr_text(full_text: str, default_category: str = "马原"):
    """
    智能解析OCR文本中的考研政治题目
    提取题号、单选/多选、题干、选项 A/B/C/D、答案与详细解析
    """
    pattern = re.compile(r'\n(?=\s*\d{1,3}\s*[\.、．，,]\s*[\u4e00-\u9fa5])')
    chunks = pattern.split(full_text)

    questions = []
    current_category = default_category

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # 检查是否切换学科
        if any(k in chunk for k in ["马克思", "唯物", "辩证", "认识论", "剩余价值", "唯物史观"]):
            current_category = "马原"
        elif any(k in chunk for k in ["毛泽东", "习近平", "中国特色社会主义", "新时代", "新质生产力"]):
            current_category = "毛中特"
        elif any(k in chunk for k in ["辛亥革命", "五四运动", "中国共产党成立", "抗日战争", "史纲"]):
            current_category = "史纲"
        elif any(k in chunk for k in ["思想道德", "法治", "人生观", "核心价值观"]):
            current_category = "思修"

        m_num = re.match(r'^\s*(\d{1,3})\s*[\.、．，,]\s*([\s\S]+)', chunk)
        if not m_num:
            continue

        q_num = int(m_num.group(1))
        body = m_num.group(2)

        # 匹配答案
        ans_m = re.search(r'(?:〖?\s*答案\s*〗?|【?\s*答案\s*】?|答案\s*[:：]|〖\s*答案)\s*([A-Da-d]+)', body)
        if not ans_m:
            continue

        answer = ans_m.group(1).upper()
        stem_and_opts = body[:ans_m.start()].strip()

        # 提取解析
        explanation = body[ans_m.end():].strip()
        explanation = re.sub(r'^[^\u4e00-\u9fa5]+', '', explanation)
        explanation = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[\u4e00-\u9fa5])', '', explanation)
        explanation = re.sub(r'[\s\n]+', ' ', explanation).strip()

        # 提取选项 A/B/C/D
        opt_re = re.compile(r'([A-D])\s*[\.、．，,\s]\s*([\s\S]*?)(?=(?:[A-D]\s*[\.、．，,\s])|\Z)')
        opt_matches = list(opt_re.finditer(stem_and_opts))

        if len(opt_matches) >= 2:
            stem = stem_and_opts[:opt_matches[0].start()].strip()
            stem = re.sub(r'[\s\n]+', ' ', stem).strip()

            options = []
            for om in opt_matches:
                k = om.group(1)
                v = om.group(2).strip()
                v = re.sub(r'[\s\n]+', ' ', v)
                v = re.sub(r'[v\'\‘\’\@\?]+$', '', v).strip()
                options.append({'key': k, 'value': v})

            q_type = "multiple" if len(answer) > 1 else "single"

            questions.append({
                "question_num": q_num,
                "question_type": q_type,
                "category": current_category,
                "stem": stem,
                "options": options,
                "answer": answer,
                "explanation": explanation
            })

    return questions

def import_to_database(workbook_name: str, questions: list, description: str = "", overwrite: bool = True):
    """将题目存入数据库"""
    if not questions:
        print("未提取到有效题目，跳过入库。")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM workbooks WHERE name = ?", (workbook_name,))
    row = cursor.fetchone()

    if row and overwrite:
        wb_id = row[0]
        # 清除旧题目重新插入
        cursor.execute("DELETE FROM questions WHERE workbook_id = ?", (wb_id,))
        cursor.execute("UPDATE workbooks SET total_questions = ?, description = ? WHERE id = ?",
                       (len(questions), description, wb_id))
    elif row:
        wb_id = row[0]
        cursor.execute("UPDATE workbooks SET total_questions = total_questions + ? WHERE id = ?",
                       (len(questions), wb_id))
    else:
        cursor.execute("""
        INSERT INTO workbooks (name, filename, file_path, total_questions, description)
        VALUES (?, ?, ?, ?, ?)
        """, (
            workbook_name,
            workbook_name + ".pdf",
            "",
            len(questions),
            description or f"已识别导入 {len(questions)} 道题目"
        ))
        wb_id = cursor.lastrowid

    cursor.execute("SELECT COALESCE(MAX(order_num), 0) FROM questions WHERE workbook_id = ?", (wb_id,))
    max_order = cursor.fetchone()[0] or 0

    for idx, q in enumerate(questions):
        cursor.execute("""
        INSERT INTO questions (workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wb_id,
            q["question_num"],
            q["question_type"],
            q["category"],
            q["stem"],
            json.dumps(q["options"], ensure_ascii=False),
            q["answer"],
            q["explanation"],
            max_order + idx + 1
        ))

    conn.commit()
    conn.close()
    print(f"成功导入 {len(questions)} 道题目至练习册【{workbook_name}】！")
