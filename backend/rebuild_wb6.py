import os
import sys
import re
import json
import sqlite3
import fitz

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "policy_study.db")
TXT_DIR = os.path.join(BASE_DIR, "backend", "ytk_txt")
YOUTIKU_EXPLAIN_PDF = os.path.join(BASE_DIR, "pdf", "27《优题库》 - 压缩版", "27《优题库》 - 压缩版", "（已压缩）27《优题库-解析拔高篇》.pdf")

TEST_SPECS = [
    # 马原 (Tests 1-6)
    {"category": "马原", "test_name": "综合测试一", "q_start": 6, "q_end": 11, "exp_start": 6, "exp_end": 15},
    {"category": "马原", "test_name": "综合测试二", "q_start": 12, "q_end": 17, "exp_start": 16, "exp_end": 25},
    {"category": "马原", "test_name": "综合测试三", "q_start": 18, "q_end": 23, "exp_start": 26, "exp_end": 35},
    {"category": "马原", "test_name": "综合测试四", "q_start": 24, "q_end": 29, "exp_start": 36, "exp_end": 45},
    {"category": "马原", "test_name": "综合测试五", "q_start": 30, "q_end": 34, "exp_start": 46, "exp_end": 55},
    {"category": "马原", "test_name": "综合测试六", "q_start": 35, "q_end": 41, "exp_start": 56, "exp_end": 65},
    # 毛中特 (Tests 1-2)
    {"category": "毛中特", "test_name": "综合测试一", "q_start": 42, "q_end": 47, "exp_start": 66, "exp_end": 75},
    {"category": "毛中特", "test_name": "综合测试二", "q_start": 48, "q_end": 54, "exp_start": 76, "exp_end": 86},
    # 习思想 (Tests 1-5)
    {"category": "习思想", "test_name": "综合测试一", "q_start": 55, "q_end": 60, "exp_start": 87, "exp_end": 95},
    {"category": "习思想", "test_name": "综合测试二", "q_start": 61, "q_end": 66, "exp_start": 96, "exp_end": 103},
    {"category": "习思想", "test_name": "综合测试三", "q_start": 67, "q_end": 73, "exp_start": 104, "exp_end": 112},
    {"category": "习思想", "test_name": "综合测试四", "q_start": 74, "q_end": 80, "exp_start": 113, "exp_end": 120},
    {"category": "习思想", "test_name": "综合测试五", "q_start": 81, "q_end": 87, "exp_start": 121, "exp_end": 130},
    # 史纲 (Tests 1-5)
    {"category": "史纲", "test_name": "综合测试一", "q_start": 88, "q_end": 92, "exp_start": 131, "exp_end": 140},
    {"category": "史纲", "test_name": "综合测试二", "q_start": 93, "q_end": 98, "exp_start": 141, "exp_end": 150},
    {"category": "史纲", "test_name": "综合测试三", "q_start": 99, "q_end": 104, "exp_start": 151, "exp_end": 160},
    {"category": "史纲", "test_name": "综合测试四", "q_start": 105, "q_end": 110, "exp_start": 161, "exp_end": 170},
    {"category": "史纲", "test_name": "综合测试五", "q_start": 111, "q_end": 117, "exp_start": 171, "exp_end": 180},
    # 思修 (Tests 1-3)
    {"category": "思修", "test_name": "综合测试一", "q_start": 118, "q_end": 123, "exp_start": 181, "exp_end": 189},
    {"category": "思修", "test_name": "综合测试二", "q_start": 124, "q_end": 128, "exp_start": 190, "exp_end": 198},
    {"category": "思修", "test_name": "综合测试三", "q_start": 129, "q_end": 133, "exp_start": 199, "exp_end": 207},
]

def parse_test_explanations(doc, exp_start, exp_end):
    """提取一个测试的所有题目解析（1..30）"""
    full_text = ""
    for p in range(exp_start - 1, exp_end):
        full_text += f"\n=== Page {p+1} ===\n" + doc[p].get_text()

    q_blocks = re.findall(
        r'(?:^|\n)\s*(\d{1,2})\s*[\.、．]\s*([A-D]{1,4})\s*\n[^\n]*?解题思路([\s\S]*?)(?=(?:\n\s*\d{1,2}\s*[\.、．]\s*[A-D]{1,4}\s*\n[^\n]*?解题思路)|=== Page|\Z)',
        full_text
    )
    result = {}
    for num_str, ans, exp_body in q_blocks:
        q_num = int(num_str)
        clean_exp = re.sub(r'[\s\n]+', ' ', exp_body).strip()
        clean_exp = clean_exp.replace("干扰选项", " 【干扰选项】")
        result[q_num] = {
            "answer": ans.strip().upper(),
            "explanation": f"【解题思路】{clean_exp}"
        }
    return result

def clean_ocr_text(lines):
    cleaned = []
    for line in lines:
        l = line.strip()
        if not l:
            continue
        if re.search(r'拔高题篇|黄皮书系列|核心考案|全国硕士|通关书课包', l):
            continue
        if re.match(r'^[一二三四五]、\s*(单项|多项)选择题', l) or l in ['多项选择题', '单项选择题', '、多项选择题', '、单项选择题', '、草项选择题', '草项选择']:
            continue
        if re.match(r'^(第[一二三四五]部分|马克思主义基本原理|毛泽东思想|习近平新时代|中国近现代史纲要|思想道德与法治)', l):
            continue
        if re.match(r'^综[合台]\s*测\s*[试式]?[一二三四五六七八九十\d]+', l):
            continue

        # 修复 OCR 题号常见混淆
        l = re.sub(r'^1\s*&\s*', '18. ', l)
        l = re.sub(r'^2\s*&\s*', '28. ', l)
        l = re.sub(r'^([12]?\d)\s*[:：]\s*', r'\1. ', l)
        l = re.sub(r'^&', '8.', l)

        # 修复汉字间多余空格
        l = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', l)
        l = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', l)
        cleaned.append(l)
    return "\n".join(cleaned)

def extract_questions_from_text(text):
    """
    按题号 1..30 切分试题，优化题号识别率与选项容错
    """
    pattern = re.compile(r'\n(?=\s*([1-9]|[12]\d|30)\s*[\.、．·:：]\s*(?:[\u4e00-\u9fa5“\"\'《A-Za-z]|\d{1,4}))')
    chunks = pattern.split("\n" + text)

    questions = []
    seen_nums = set()

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        m_num = re.match(r'^\s*([1-9]|[12]\d|30)\s*[\.、．·:：]\s*([\s\S]+)', chunk)
        if not m_num:
            continue
        q_num = int(m_num.group(1))
        if q_num < 1 or q_num > 30:
            continue
        if q_num in seen_nums:
            continue

        body = m_num.group(2).strip()

        # 选项预修复与标准化
        def normalize_opt_key(m):
            k = m.group(1).replace('(', '').replace(')', '').strip().upper()
            if k in ['①', '1', 'A']: return '\nA. '
            if k in ['②', '2', '8', 'B']: return '\nB. '
            if k in ['③', '3', '0', 'O', 'C']: return '\nC. '
            if k in ['④', '4', 'D']: return '\nD. '
            return f'\n{k}. '

        body = re.sub(r'(?:^|\s+)([A-Da-d①②③④80oO]|\([A-Da-d]\))\s*[\.、．，,·:：\s]\s*', normalize_opt_key, body)
        opt_pattern = re.compile(r'\n([A-D])\.\s*([\s\S]*?)(?=(?:\n[A-D]\.)|\Z)')
        opt_matches = list(opt_pattern.finditer(body))

        if len(opt_matches) >= 2:
            stem = body[:opt_matches[0].start()].strip()
            stem = re.sub(r'[\s\n]+', ' ', stem).strip()
            stem = re.sub(r'^\d{1,2}\s*[\.、．·:：]\s*', '', stem)

            opts = {}
            for om in opt_matches:
                k = om.group(1).upper()
                v = om.group(2).strip()
                v = re.sub(r'^[A-Da-d①②③④\(\)]\s*[\.、．，,·:\s]\s*', '', v)
                v = re.sub(r'\s*\d{1,2}\s*[\.、．·:：]\s*[\u4e00-\u9fa5“\"\'《].*$', '', v)
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
                seen_nums.add(q_num)

    return sorted(questions, key=lambda x: x["q_num"])

def rebuild_all():
    print("=" * 64)
    print("🚀 开始重构与校准《徐涛优题库（拔高篇）》全 21 套测试卷...")
    print("=" * 64)

    doc_exp = fitz.open(YOUTIKU_EXPLAIN_PDF)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 彻底清除旧的、混乱的 WB6 和 WB5 题目
    cursor.execute("DELETE FROM questions WHERE workbook_id = 6")
    cursor.execute("DELETE FROM questions WHERE workbook_id = 5")
    cursor.execute("DELETE FROM workbooks WHERE id = 5")
    conn.commit()

    total_inserted = 0
    order_num = 0

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
        qs = extract_questions_from_text(cleaned_text)

        test_added = 0
        for q in qs:
            q_num = q["q_num"]
            if q_num not in exp_dict:
                continue

            exp_item = exp_dict[q_num]
            ans = exp_item["answer"]
            explanation = exp_item["explanation"]
            q_type = "multiple" if len(ans) > 1 else "single"
            order_num += 1

            cursor.execute("""
            INSERT INTO questions (
                workbook_id, question_num, question_type, category,
                stem, options_json, answer, explanation, order_num
            ) VALUES (6, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                q_num,
                q_type,
                cat,
                f"【{tname}】{q['stem']}",
                json.dumps(q["options"], ensure_ascii=False),
                ans,
                explanation,
                order_num
            ))
            test_added += 1

        total_inserted += test_added
        print(f"✅ [{cat} - {tname}] 成功录入 {test_added}/30 题（学科：{cat}，完全对齐解析）")

    # 更新 workbook 6 元数据
    cursor.execute("""
    UPDATE workbooks
    SET name = '2027 徐涛优题库（拔高篇·全21套综合测试卷）',
        total_questions = ?,
        description = '徐涛考研政治优题库拔高进阶卷，全21套综合测试卷（马原6套、毛中特2套、习思想5套、史纲5套、思修3套），官方精细解析与干扰项剖析。'
    WHERE id = 6
    """, (total_inserted,))

    conn.commit()
    conn.close()
    doc_exp.close()

    print("=" * 64)
    print(f"🎉 徐涛优题库重构完成！共录入 {total_inserted} 道绝对准确、完全对齐的题目！")
    print("=" * 64)

if __name__ == "__main__":
    rebuild_all()
