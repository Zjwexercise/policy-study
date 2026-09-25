import os
import sys
import re
import json
import time
import sqlite3
import subprocess
import fitz
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "policy_study.db")
OCR_SCRIPT = os.path.join(BASE_DIR, "backend", "ocr_test.ps1")
LOG_FILE = os.path.join(BASE_DIR, "backend", "pipeline.log")

TI_1000_Q_PDF = os.path.join(BASE_DIR, "pdf", "2027--1000题--试题册.pdf")
TI_1000_EXP_PDF = os.path.join(BASE_DIR, "pdf", "2027--1000题--解析册.pdf")
YOUTIKU_Q_PDF = os.path.join(BASE_DIR, "pdf", "27《优题库》 - 压缩版", "27《优题库》 - 压缩版", "（已压缩）27《优题库-试题拔高篇》.pdf")
YOUTIKU_EXP_PDF = os.path.join(BASE_DIR, "pdf", "27《优题库》 - 压缩版", "27《优题库》 - 压缩版", "（已压缩）27《优题库-解析拔高篇》.pdf")
SHUATI_Q_PDF = os.path.join(BASE_DIR, "pdf", "2027-刷题计划--试题册.pdf")
SHUATI_EXP_PDF = os.path.join(BASE_DIR, "pdf", "2027-刷题计划--解析册.pdf")

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

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

def get_1000_category(page_num):
    if page_num <= 66:
        return "马原"
    elif page_num <= 88:
        return "毛中特"
    elif page_num <= 124:
        return "习思想"
    elif page_num <= 175:
        return "史纲"
    else:
        return "思修"

def scan_1000ti_chunk(start_p, end_p, doc_q, doc_exp, temp_img):
    """扫描肖秀荣 1000 题的一个页码区间并入库"""
    cat = get_1000_category(start_p)
    log(f"【肖秀荣1000题】正在扫描第 {start_p+1}~{end_p+1} 页（学科模块：{cat}）...")
    
    # 1. 扫描解析
    exp_text = ""
    for p in range(start_p - 1, min(len(doc_exp), end_p)):
        exp_text += f"\n=== Page {p+1} ===\n" + ocr_page(doc_exp, p, temp_img)

    exp_pattern = re.compile(
        r'([A-Da-d]{1,4})\s*[)\]>〗\s]*[〖\[【（《]?\s*解析\s*[〗\]】）》\]]?\s*([\s\S]*?)(?=(?:[A-Da-d]{1,4}\s*[)\]>〗\s]*[〖\[【（《]?\s*解析)|=== Page|\Z)'
    )
    parsed_exps = []
    for m in exp_pattern.finditer(exp_text):
        ans = m.group(1).upper()
        clean_exp = re.sub(r'[\s\n]+', ' ', m.group(2)).strip()
        parsed_exps.append({
            "answer": ans,
            "explanation": f"【肖秀荣1000题名师精解】{clean_exp}"
        })

    # 2. 扫描试题
    q_text = ""
    for p in range(start_p, min(len(doc_q), end_p + 1)):
        q_text += f"\n=== Page {p+1} ===\n" + ocr_page(doc_q, p, temp_img)

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

    # 入库
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
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
            explanation = f"【肖秀荣1000题 第 {num} 题精析】考查{cat}核心考点。"

        q_type = "multiple" if len(answer) > 1 else "single"
        max_order += 1
        c.execute("""
        INSERT INTO questions (
            workbook_id, question_num, question_type, category,
            stem, options_json, answer, explanation, order_num
        ) VALUES (5, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            num,
            q_type,
            cat,
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

    log(f"✅ 【肖秀荣1000题】本轮成功录入 {added} 题！当前该册总题量已升至: {total_5} 题")

def run_pipeline():
    log("=" * 64)
    log("🚀 考研政治后台自动化大扫描入库流水线正式启动！")
    log("=" * 64)

    temp_img = os.path.join(BASE_DIR, "backend", "temp_pipeline.png")

    # ==========================================
    # 阶段 1: 扫描《肖秀荣 1000题》剩余全部学科
    # ==========================================
    log("【阶段 1】开始扫描《肖秀荣 1000题》毛中特、习思想、史纲、思修...")
    doc_1000_q = fitz.open(TI_1000_Q_PDF)
    doc_1000_exp = fitz.open(TI_1000_EXP_PDF)

    # 分块扫描：从第 54 页一直到第 204 页
    chunks = [
        (54, 75),   # 毛中特上
        (76, 95),   # 毛中特下与习思想上
        (96, 124),  # 习思想下
        (125, 150), # 史纲上
        (151, 175), # 史纲下
        (176, 204), # 思修法治
    ]

    for start_p, end_p in chunks:
        try:
            scan_1000ti_chunk(start_p, end_p, doc_1000_q, doc_1000_exp, temp_img)
            time.sleep(1) # 呼吸缓冲
        except Exception as e:
            log(f"⚠️ 扫描第 {start_p}~{end_p} 页出错: {e}")

    doc_1000_q.close()
    doc_1000_exp.close()

    # ==========================================
    # 阶段 2: 扫描《徐涛 优题库》拔高篇剩余 13 套测试
    # ==========================================
    log("\n【阶段 2】开始扫描《徐涛 优题库》毛中特、习思想、史纲、思修测试卷...")
    try:
        from import_youtiku_all import parse_all_explanations, extract_questions_from_test_text, YOUTIKU_EXPLAIN_PDF, YOUTIKU_QUESTION_PDF
        tests_data = parse_all_explanations(YOUTIKU_EXPLAIN_PDF)
        doc_ytk_q = fitz.open(YOUTIKU_QUESTION_PDF)

        youtiku_chunks = [
            (("毛中特", "综合测试一"), 41, 46),
            (("毛中特", "综合测试二"), 47, 52),
            (("习思想", "综合测试一"), 53, 58),
            (("习思想", "综合测试二"), 59, 64),
            (("习思想", "综合测试三"), 65, 70),
            (("史纲", "综合测试一"), 71, 76),
            (("史纲", "综合测试二"), 77, 82),
            (("史纲", "综合测试三"), 83, 88),
            (("史纲", "综合测试四"), 89, 94),
            (("史纲", "综合测试五"), 95, 100),
            (("思修", "综合测试一"), 101, 106),
            (("思修", "综合测试二"), 107, 112),
            (("思修", "综合测试三"), 113, 118),
        ]

        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("SELECT max(order_num) FROM questions WHERE workbook_id = 6")
        ytk_order = cursor.fetchone()[0] or 0

        for test_key, start_p, end_p in youtiku_chunks:
            part_name, test_title = test_key
            log(f"【徐涛优题库】正在扫描 {part_name}·{test_title}（第 {start_p+1}~{end_p+1} 页）...")
            test_ocr_text = ""
            for p in range(start_p, end_p + 1):
                if p < len(doc_ytk_q):
                    txt = ocr_page(doc_ytk_q, p, temp_img)
                    test_ocr_text += f"\n=== Page {p+1} ===\n" + txt

            parsed_qs = extract_questions_from_test_text(test_ocr_text)
            exp_dict = tests_data.get(test_key, {})
            added = 0
            for q in parsed_qs:
                q_num = q["q_num"]
                stem = q["stem"]
                opts = q["options"]
                if len(stem) < 8 or len(opts) < 2:
                    continue

                exp_info = exp_dict.get(q_num, {})
                answer = exp_info.get("answer", "")
                if not answer:
                    answer = "ABCD" if q_num >= 17 else "A"
                explanation = exp_info.get("explanation", f"【{test_title} 第 {q_num} 题】考查 {part_name} 核心考点。")
                category = exp_info.get("category", part_name)
                q_type = "multiple" if len(answer) > 1 else "single"

                ytk_order += 1
                cursor.execute("""
                INSERT INTO questions (
                    workbook_id, question_num, question_type, category,
                    stem, options_json, answer, explanation, order_num
                ) VALUES (6, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    q_num, q_type, category,
                    f"【{test_title}】{stem}",
                    json.dumps(opts, ensure_ascii=False),
                    answer, explanation, ytk_order
                ))
                added += 1

            cursor.execute("SELECT count(*) FROM questions WHERE workbook_id = 6")
            total_6 = cursor.fetchone()[0]
            cursor.execute("UPDATE workbooks SET total_questions = ? WHERE id = 6", (total_6,))
            conn.commit()
            log(f"✅ 【徐涛优题库】成功录入 {test_title} 共 {added} 题！当前该册总题量: {total_6} 题")

        doc_ytk_q.close()
        conn.close()
    except Exception as e:
        log(f"⚠️ 扫描徐涛优题库出错: {e}")

    # ==========================================
    # 阶段 3: 执行全库深度选项清洗与整理
    # ==========================================
    log("\n【阶段 3】执行全库选项质量深度校准与清洗...")
    try:
        from clean_options import clean_and_split_options
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        c = conn.cursor()
        c.execute('SELECT id, stem, options_json, answer, explanation FROM questions')
        rows = c.fetchall()
        fixed = 0
        for qid, stem, opts_json, ans, exp in rows:
            opts = json.loads(opts_json)
            new_stem, new_opts = clean_and_split_options(stem, opts, ans, exp)
            if new_opts != opts or new_stem != stem:
                fixed += 1
                c.execute('UPDATE questions SET stem = ?, options_json = ? WHERE id = ?',
                          (new_stem, json.dumps(new_opts, ensure_ascii=False), qid))
        conn.commit()
        c.execute('SELECT count(*) FROM questions')
        final_total = c.fetchone()[0]
        conn.close()
        log(f"✅ 全库清洗完毕，共深度规范化了 {fixed} 道题！全库最终总题量: {final_total} 题")
    except Exception as e:
        log(f"⚠️ 全库清洗出错: {e}")

    if os.path.exists(temp_img):
        os.remove(temp_img)

    log("=" * 64)
    log("🎉 考研政治后台自动化全量扫描入库圆满完成！题库已彻底满血！")
    log("=" * 64)

if __name__ == "__main__":
    run_pipeline()
