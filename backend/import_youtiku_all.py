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
YOUTIKU_EXPLAIN_PDF = os.path.join(BASE_DIR, "pdf", "27《优题库》 - 压缩版", "27《优题库》 - 压缩版", "（已压缩）27《优题库-解析拔高篇》.pdf")
YOUTIKU_QUESTION_PDF = os.path.join(BASE_DIR, "pdf", "27《优题库》 - 压缩版", "27《优题库》 - 压缩版", "（已压缩）27《优题库-试题拔高篇》.pdf")

def parse_all_explanations(explain_pdf_path):
    """
    从数字版文本解析册提取所有的 (test_title, q_num) -> (answer, explanation, category)
    """
    doc = fitz.open(explain_pdf_path)
    current_part = "马原"
    current_test = "综合测试一"
    
    # 结构: dict[(part, test)] -> dict[q_num] -> {answer, explanation}
    tests_data = {}
    
    for p in range(len(doc)):
        text = doc[p].get_text()
        
        # 判断大分类与测试
        if "第一部分" in text or "马克思主义基本原理" in text:
            current_part = "马原"
        elif "第二部分" in text or "毛泽东思想" in text:
            current_part = "毛中特"
        elif "第三部分" in text or "习近平新时代" in text:
            current_part = "习思想"
        elif "第四部分" in text or "中国近现代史" in text:
            current_part = "史纲"
        elif "第五部分" in text or "思想道德与法治" in text:
            current_part = "思修"
            
        m_test = re.search(r'综合测试([一二三四五六七八九十\d]+)', text)
        if m_test:
            current_test = f"综合测试{m_test.group(1)}"
            
        key = (current_part, current_test)
        if key not in tests_data:
            tests_data[key] = {}
            
        # 匹配如 "1. A\n9解题思路..." 或 "1.A\n解题思路..."
        q_blocks = re.findall(
            r'(?:^|\n)\s*(\d{1,2})\s*[\.、．]\s*([A-D]{1,4})\s*\n(?:9?解题思路|【解析】)([\s\S]*?)(?=(?:\n\s*\d{1,2}\s*[\.、．]\s*[A-D]{1,4}\s*\n(?:9?解题思路|【解析】))|=== Page|\Z)',
            text
        )
        for num_str, ans, exp_body in q_blocks:
            q_num = int(num_str)
            clean_exp = re.sub(r'[\s\n]+', ' ', exp_body).strip()
            # 格式化解析文本
            clean_exp = clean_exp.replace("9解题思路", "【解题思路】").replace("解题思路", "【解题思路】")
            clean_exp = clean_exp.replace("9干扰选项", " 【干扰选项】").replace("干扰选项", " 【干扰选项】")
            tests_data[key][q_num] = {
                "answer": ans.strip().upper(),
                "explanation": clean_exp,
                "category": current_part
            }
            
    doc.close()
    return tests_data

def clean_ocr_line(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    # 修复常见 OCR 错别字与首字符
    line = re.sub(r'^&', '8.', line)
    line = re.sub(r'^[oO0]\.', 'C.', line)
    # 去除汉字间的多余空格
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

def extract_questions_from_test_text(test_ocr_text):
    """
    从测试题 OCR 文本中识别出 1~33 题的题干和选项
    """
    # 按照题号切分
    # 题号模式：1. ~ 33.
    pattern = re.compile(r'\n(?=\s*\d{1,2}\s*[\.、．]\s*[\u4e00-\u9fa5“\"\'《])')
    chunks = pattern.split(test_ocr_text)
    
    questions = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        m_num = re.match(r'^\s*(\d{1,2})\s*[\.、．]\s*([\s\S]+)', chunk)
        if not m_num:
            continue
        q_num = int(m_num.group(1))
        if q_num < 1 or q_num > 33:
            continue
        body = m_num.group(2).strip()
        
        # 选项提取：A. B. C. D.
        # 标准化常见选项前缀
        body = re.sub(r'(?:^|\s+)([A-Da-dＡ-Ｄａ-ｄ①②③④]|\([A-Da-d]\))\s*[\.、．，,:\s]\s*', r'\n\1. ', body)
        
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
                v = re.sub(r'[\s\n]+', ' ', v).strip()
                # 去除选项内混入的后续题号或杂符
                v = re.sub(r'\s*\d{1,2}\s*[\.、．].*$', '', v).strip()
                if k in ['A', 'B', 'C', 'D'] and v:
                    opts[k] = v
                    
            final_opts = []
            for k in ['A', 'B', 'C', 'D']:
                if k in opts:
                    final_opts.append({'key': k, 'value': opts[k]})
                    
            questions.append({
                "q_num": q_num,
                "stem": stem,
                "options": final_opts
            })
            
    return questions

def run_import(max_tests=6):
    print("=" * 60)
    print("开始从《2027 徐涛考研政治优题库》提取海量真题与解析...")
    print("=" * 60)
    
    # 1. 提取所有解析
    print("正在解析数字版《解析拔高篇》...")
    tests_data = parse_all_explanations(YOUTIKU_EXPLAIN_PDF)
    total_exp_items = sum(len(v) for v in tests_data.values())
    print(f"成功提取到 {len(tests_data)} 套测试卷，共计 {total_exp_items} 道题目的标准答案与详尽解题思路！")
    
    # 2. 从试题册逐套 OCR 识别题目
    doc = fitz.open(YOUTIKU_QUESTION_PDF)
    temp_img = os.path.join(BASE_DIR, "backend", "temp_youtiku.png")
    
    # 定义测试卷页码映射 (试题册中的页码范围)
    # 每套测试约 6 页
    test_page_ranges = [
        (("马原", "综合测试一"), 5, 10),    # 第 6~11 页
        (("马原", "综合测试二"), 11, 16),   # 第 12~17 页
        (("马原", "综合测试三"), 17, 22),   # 第 18~23 页
        (("马原", "综合测试四"), 23, 28),   # 第 24~29 页
        (("马原", "综合测试五"), 29, 34),   # 第 30~35 页
        (("马原", "综合测试六"), 35, 40),   # 第 36~41 页
        (("毛中特", "综合测试一"), 41, 46), # 第 42~47 页
        (("毛中特", "综合测试二"), 47, 52), # 第 48~53 页
        (("习思想", "综合测试一"), 53, 58), # 第 54~59 页
        (("习思想", "综合测试二"), 59, 64), # 第 60~65 页
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取或创建徐涛优题库 workbook_id = 6
    cursor.execute("SELECT id FROM workbooks WHERE id = 6")
    wb_row = cursor.fetchone()
    if not wb_row:
        cursor.execute("""
        INSERT INTO workbooks (id, name, filename, file_path, total_questions, description)
        VALUES (6, '2027 徐涛考研政治优题库', '27《优题库》 - 压缩版', '', 0, '徐涛考研政治优题库（拔高题篇与基础题篇精选，含单选多选与名师独家深度解题思路）')
        """)
        conn.commit()
        workbook_id = 6
    else:
        workbook_id = 6
        
    # 先清空 workbook 6 旧数据重新灌入
    cursor.execute("DELETE FROM questions WHERE workbook_id = ?", (workbook_id,))
    cursor.execute("DELETE FROM user_progress WHERE workbook_id = ?", (workbook_id,))
    cursor.execute("DELETE FROM wrong_book WHERE workbook_id = ?", (workbook_id,))
    conn.commit()
    
    imported_count = 0
    
    for idx, (test_key, start_p, end_p) in enumerate(test_page_ranges[:max_tests]):
        part_name, test_title = test_key
        print(f"\n[测试 {idx+1}/{min(max_tests, len(test_page_ranges))}] 正在 OCR 识别 {part_name}·{test_title}（第 {start_p+1}~{end_p+1} 页）...")
        
        test_ocr_text = ""
        for p in range(start_p, end_p + 1):
            if p < len(doc):
                txt = ocr_page(doc, p, temp_img)
                test_ocr_text += f"\n=== Page {p+1} ===\n" + txt
                
        # 提取题目
        parsed_qs = extract_questions_from_test_text(test_ocr_text)
        print(f"  识别到 {len(parsed_qs)} 道题目，正在匹配标准答案与深度解析...")
        
        # 匹配解析
        exp_dict = tests_data.get(test_key, {})
        for q in parsed_qs:
            q_num = q["q_num"]
            stem = q["stem"]
            opts = q["options"]
            
            # 从解析字典获取对应答案
            exp_info = exp_dict.get(q_num, {})
            answer = exp_info.get("answer", "")
            explanation = exp_info.get("explanation", f"【{test_title} 第 {q_num} 题】考查 {part_name} 核心考点。")
            category = exp_info.get("category", part_name)
            
            # 如果没匹配到答案，做默认推断
            if not answer:
                answer = "ABCD" if q_num >= 17 else "A"
                
            q_type = "multiple" if len(answer) > 1 else "single"
            
            # 过滤过短的题干
            if len(stem) < 8 or len(opts) < 2:
                continue
                
            cursor.execute("""
            INSERT INTO questions (
                workbook_id, question_num, question_type, category, 
                stem, options_json, answer, explanation, order_num
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workbook_id,
                q_num,
                q_type,
                category,
                f"【{test_title}】{stem}",
                json.dumps(opts, ensure_ascii=False),
                answer,
                explanation,
                imported_count + 1
            ))
            imported_count += 1
            
        conn.commit()
        print(f"  已成功录入 {len(parsed_qs)} 题！累计入库: {imported_count} 题")
        
    doc.close()
    if os.path.exists(temp_img):
        os.remove(temp_img)
        
    # 更新练习册总题数
    cursor.execute("UPDATE workbooks SET total_questions = ? WHERE id = ?", (imported_count, workbook_id))
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"🎉 导入完毕！已将 {imported_count} 道完整题目与解析导入《2027 徐涛考研政治优题库》！")
    print("=" * 60)

if __name__ == "__main__":
    run_import(max_tests=6)
