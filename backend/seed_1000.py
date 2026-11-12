import os
import sys
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "policy_study.db")

WB_METAS = [
    {
        "id": 34,
        "name": "【1000题】第一部分 马克思主义基本原理 (马原)",
        "filename": "1000_mayuan.pdf",
        "file_path": "1000题",
        "total_questions": 277,
        "description": "2027版考研政治精雕细刻1000题 · 第一部分 马克思主义基本原理（哲学、政经、科社全章节客观题精练）"
    },
    {
        "id": 35,
        "name": "【1000题】第二部分 毛中特理论体系概论 (毛中特)",
        "filename": "1000_maozhongte.pdf",
        "file_path": "1000题",
        "total_questions": 99,
        "description": "2027版考研政治精雕细刻1000题 · 第二部分 毛泽东思想和中国特色社会主义理论体系概论"
    },
    {
        "id": 36,
        "name": "【1000题】第三部分 习近平新时代中特思想概论 (习思想)",
        "filename": "1000_xisixiang.pdf",
        "file_path": "1000题",
        "total_questions": 199,
        "description": "2027版考研政治精雕细刻1000题 · 第三部分 习近平新时代中国特色社会主义思想概论（17章全核心题集）"
    },
    {
        "id": 37,
        "name": "【1000题】第四部分 中国近现代史纲要 (史纲)",
        "filename": "1000_shigang.pdf",
        "file_path": "1000题",
        "total_questions": 239,
        "description": "2027版考研政治精雕细刻1000题 · 第四部分 中国近现代史纲要（近现代历史时间线核心考点题）"
    },
    {
        "id": 38,
        "name": "【1000题】第五部分 思想道德与法治 (思修)",
        "filename": "1000_sixiu.pdf",
        "file_path": "1000题",
        "total_questions": 132,
        "description": "2027版考研政治精雕细刻1000题 · 第五部分 思想道德与法治（人生观、理想信念、法治精神核心题）"
    },
    {
        "id": 39,
        "name": "【1000题】精雕细刻1000题全科目精选合集",
        "filename": "1000_master.pdf",
        "file_path": "1000题",
        "total_questions": 946,
        "description": "2027版考研政治精雕细刻1000题 · 全五大科目（马原、毛中特、习思想、史纲、思修）综合合集共 946 题"
    }
]

def find_data_dir():
    candidates = [
        os.path.join(BASE_DIR, "..", "frontend", "dist", "data"),
        os.path.join(BASE_DIR, "..", "frontend", "public", "data"),
        "/var/www/policy-study/frontend/dist/data",
        "/var/www/policy-study/frontend/public/data"
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.exists(os.path.join(c, "questions_39.json")):
            return os.path.abspath(c)
    return None

def check_and_seed_1000(db_path=None):
    if db_path is None:
        db_path = DB_PATH
        
    if not os.path.exists(db_path):
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 检查 workbook 39 是否已完整就绪且选项格式为最新的标准列表
    try:
        c.execute("SELECT count(*) FROM questions WHERE workbook_id = 39")
        cnt = c.fetchone()[0]
        c.execute("SELECT options_json, question_type FROM questions WHERE workbook_id = 39 LIMIT 1")
        row = c.fetchone()
        if cnt >= 940 and row and row[0] and row[0].strip().startswith("[") and row[1] in ["single", "multiple"]:
            # 已经有符合标准的题库了，无需重复注入
            conn.close()
            return
    except Exception as e:
        print("[seed_1000] 检查题库状态:", e)
        
    data_dir = find_data_dir()
    if not data_dir:
        print("[-] 未找到 1000 题 JSON 静态数据目录，跳过注入")
        conn.close()
        return

    print(f"==========================================================")
    print(f" 🚀 正在向数据库自动注入《2027精雕细刻1000题》全套数据...")
    print(f"    数据来源目录: {data_dir}")
    print(f"    目标数据库: {db_path}")
    print(f"==========================================================")
    
    for meta in WB_METAS:
        wb_id = meta["id"]
        # 1. 插入或更新 workbook
        c.execute("SELECT id FROM workbooks WHERE id = ?", (wb_id,))
        if c.fetchone():
            c.execute("""
                UPDATE workbooks 
                SET name = ?, filename = ?, file_path = ?, total_questions = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (meta["name"], meta["filename"], meta["file_path"], meta["total_questions"], meta["description"], wb_id))
        else:
            c.execute("""
                INSERT INTO workbooks (id, name, filename, file_path, total_questions, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (wb_id, meta["name"], meta["filename"], meta["file_path"], meta["total_questions"], meta["description"]))
            
        # 2. 读取对应 JSON 插入题目
        json_file = os.path.join(data_dir, f"questions_{wb_id}.json")
        if not os.path.exists(json_file):
            print(f"[-] 缺失题库文件: {json_file}")
            continue
            
        with open(json_file, encoding="utf-8") as f:
            qs = json.load(f)
            
        # 清除该 workbook 旧题目，重新灌入
        c.execute("DELETE FROM questions WHERE workbook_id = ?", (wb_id,))
        
        q_rows = []
        for idx, q in enumerate(qs, 1):
            opts = q.get("options", [])
            if isinstance(opts, dict):
                opts = [{"key": k, "value": v} for k, v in opts.items()]
            elif isinstance(opts, str):
                try:
                    parsed = json.loads(opts)
                    if isinstance(parsed, dict):
                        opts = [{"key": k, "value": v} for k, v in parsed.items()]
                    elif isinstance(parsed, list):
                        opts = parsed
                except:
                    pass
            opts_json = json.dumps(opts, ensure_ascii=False)

            q_type = q.get("question_type", "single")
            if q_type in ["单选题", "单选"]:
                q_type = "single"
            elif q_type in ["多选题", "多选"]:
                q_type = "multiple"
            elif not q_type:
                q_type = "multiple" if len(q.get("answer", "A")) > 1 else "single"

            qid = q.get("id")
            if isinstance(qid, int):
                q_rows.append((
                    qid,
                    wb_id,
                    idx,
                    q_type,
                    q.get("category", "综合"),
                    q.get("stem", ""),
                    opts_json,
                    q.get("answer", "A"),
                    q.get("explanation", ""),
                    idx
                ))
            else:
                q_rows.append((
                    None,
                    wb_id,
                    idx,
                    q_type,
                    q.get("category", "综合"),
                    q.get("stem", ""),
                    opts_json,
                    q.get("answer", "A"),
                    q.get("explanation", ""),
                    idx
                ))
            
        c.executemany("""
            INSERT OR REPLACE INTO questions (id, workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, q_rows)
        print(f" [+] 成功注入: {meta['name']} -> {len(q_rows)} 题")
        
    conn.commit()
    conn.close()
    print(" 🎉《2027精雕细刻1000题》全套 946 题成功自动同步至数据库！")

if __name__ == "__main__":
    check_and_seed_1000()
