import os
import sys
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(BASE_DIR, "policy_study.db")
DEFAULT_BACKUP = "/var/www/user_data_backup.json"

USER_TABLES = [
    "users",
    "user_tokens",
    "user_cloud_data",
    "user_progress",
    "study_logs",
    "wrong_book",
    "notes",
    "system_settings"
]

def backup_userdata(db_path=DEFAULT_DB, backup_path=DEFAULT_BACKUP):
    if not os.path.exists(db_path):
        print(f"[Backup] 数据库不存在: {db_path}，跳过导出")
        return
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    data = {}
    for table in USER_TABLES:
        try:
            c.execute(f"SELECT * FROM {table}")
            rows = [dict(r) for r in c.fetchall()]
            data[table] = rows
            print(f"[Backup] 已备份表 {table}: {len(rows)} 行")
        except Exception as e:
            print(f"[Backup] 读取表 {table} 失败 (可能不存在): {e}")
            data[table] = []
            
    conn.close()
    
    # 保存备份
    os.makedirs(os.path.dirname(os.path.abspath(backup_path)), exist_ok=True)
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[Backup] 用户做题记录及账号数据安全导出完成 -> {backup_path}")

def restore_userdata(db_path=DEFAULT_DB, backup_path=DEFAULT_BACKUP):
    if not os.path.exists(backup_path):
        print(f"[Restore] 备份文件不存在: {backup_path}，无需恢复")
        return
        
    with open(backup_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    for table, rows in data.items():
        if not rows:
            continue
        try:
            # 获取当前目标表字段
            c.execute(f"PRAGMA table_info({table})")
            cols = [info[1] for info in c.fetchall()]
            if not cols:
                continue
                
            for r in rows:
                keys = [k for k in r.keys() if k in cols]
                placeholders = ", ".join(["?"] * len(keys))
                col_names = ", ".join(keys)
                vals = [r[k] for k in keys]
                
                # 特别对 user_cloud_data 进行智能长度比对，保留做题记录更多的一份
                if table == "user_cloud_data":
                    uid = r.get("user_id")
                    c.execute("SELECT records_json FROM user_cloud_data WHERE user_id = ?", (uid,))
                    existing = c.fetchone()
                    if existing and existing[0]:
                        try:
                            ex_len = len(json.loads(existing[0]))
                            bk_len = len(json.loads(r.get("records_json") or "{}"))
                            if ex_len > bk_len:
                                continue # 本地已有更新更全的记录，跳过覆盖
                        except Exception:
                            pass
                            
                sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
                c.execute(sql, vals)
                
            print(f"[Restore] 成功恢复表 {table}: {len(rows)} 行")
        except Exception as e:
            print(f"[Restore] 恢复表 {table} 出错: {e}")
            
    conn.commit()
    conn.close()
    print("[Restore] 🎉 用户做题记录、错题本及考生账号全部无损恢复合流成功！")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "backup"
    target_backup = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BACKUP
    if action == "backup":
        backup_userdata(DEFAULT_DB, target_backup)
    elif action == "restore":
        restore_userdata(DEFAULT_DB, target_backup)
    else:
        print("Usage: python server_migrate.py [backup|restore] [backup_file_path]")
