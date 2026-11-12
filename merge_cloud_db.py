import os
import sys
import sqlite3

def merge():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backup_db = "/var/www/policy_study.db.safe_backup"
    target_db = os.path.join(base_dir, "backend", "policy_study.db")
    
    if not os.path.exists(target_db):
        print(f"[-] 目标数据库不存在: {target_db}")
        return

    if not os.path.exists(backup_db):
        print(f"[*] 备份数据库不存在，使用全新题库: {backup_db}")
        return

    print("==========================================================")
    print(" 🔄 正在智能双向融合：云端用户做题数据 + 2027最新1000题库...")
    print("==========================================================")
    
    b_conn = sqlite3.connect(backup_db)
    b_c = b_conn.cursor()
    
    t_conn = sqlite3.connect(target_db)
    t_c = t_conn.cursor()
    
    # 1. 迁移 users
    try:
        users = b_c.execute("SELECT id, username, password_hash, created_at FROM users").fetchall()
        t_c.executemany("INSERT OR REPLACE INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)", users)
        print(f" [+] 用户账号恢复: {len(users)} 个")
    except Exception as e:
        print(" [-] users migration notice:", e)

    # 2. 迁移 user_tokens
    try:
        tokens = b_c.execute("SELECT token, user_id, created_at FROM user_tokens").fetchall()
        t_c.executemany("INSERT OR REPLACE INTO user_tokens (token, user_id, created_at) VALUES (?, ?, ?)", tokens)
        print(f" [+] 用户登录态恢复: {len(tokens)} 个")
    except Exception as e:
        print(" [-] tokens migration notice:", e)

    # 3. 迁移 user_progress
    try:
        prog = b_c.execute("SELECT id, user_id, question_id, user_answer, is_correct, answered_at FROM user_progress").fetchall()
        t_c.executemany("INSERT OR REPLACE INTO user_progress (id, user_id, question_id, user_answer, is_correct, answered_at) VALUES (?, ?, ?, ?, ?, ?)", prog)
        print(f" [+] 正式做题记录恢复: {len(prog)} 条")
    except Exception as e:
        print(" [-] progress migration notice:", e)

    # 4. 迁移 wrong_book
    try:
        wrong = b_c.execute("SELECT id, user_id, question_id, wrong_count, is_mastered, last_wrong_at FROM wrong_book").fetchall()
        t_c.executemany("INSERT OR REPLACE INTO wrong_book (id, user_id, question_id, wrong_count, is_mastered, last_wrong_at) VALUES (?, ?, ?, ?, ?, ?)", wrong)
        print(f" [+] 错题本记录恢复: {len(wrong)} 条")
    except Exception as e:
        print(" [-] wrong_book migration notice:", e)

    # 5. 迁移 notes
    try:
        notes = b_c.execute("SELECT id, user_id, question_id, content, updated_at FROM notes").fetchall()
        t_c.executemany("INSERT OR REPLACE INTO notes (id, user_id, question_id, content, updated_at) VALUES (?, ?, ?, ?, ?)", notes)
        print(f" [+] 考点笔记恢复: {len(notes)} 条")
    except Exception as e:
        print(" [-] notes migration notice:", e)

    # 6. 迁移 study_logs
    try:
        logs = b_c.execute("SELECT id, user_id, duration_seconds, log_date FROM study_logs").fetchall()
        t_c.executemany("INSERT OR REPLACE INTO study_logs (id, user_id, duration_seconds, log_date) VALUES (?, ?, ?, ?)", logs)
        print(f" [+] 学习时长恢复: {len(logs)} 条")
    except Exception as e:
        print(" [-] study_logs migration notice:", e)

    # 7. 迁移 user_cloud_data
    try:
        cdata = b_c.execute("SELECT user_id, data_json, updated_at FROM user_cloud_data").fetchall()
        t_c.executemany("INSERT OR REPLACE INTO user_cloud_data (user_id, data_json, updated_at) VALUES (?, ?, ?)", cdata)
        print(f" [+] 云端同步备份记录恢复: {len(cdata)} 条")
    except Exception as e:
        print(" [-] user_cloud_data migration notice:", e)

    t_conn.commit()
    t_conn.close()
    b_conn.close()
    print(" 🎉 融合完成！做题数据无缝保留，1000题题库同步上线！")

if __name__ == "__main__":
    merge()
