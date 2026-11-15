import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "policy_study.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 练习册表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workbooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        filename TEXT,
        file_path TEXT,
        total_questions INTEGER DEFAULT 0,
        description TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 题目表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workbook_id INTEGER NOT NULL,
        question_num INTEGER NOT NULL,
        question_type TEXT NOT NULL, -- 'single' (单选) or 'multiple' (多选)
        category TEXT DEFAULT '综合', -- '马原', '毛中特', '史纲', '思修', '时政', '综合'
        stem TEXT NOT NULL,
        options_json TEXT NOT NULL, -- JSON array of options: [{"key": "A", "value": "..."}, ...]
        answer TEXT NOT NULL, -- e.g. "A", "ABCD"
        explanation TEXT DEFAULT '',
        order_num INTEGER DEFAULT 0,
        FOREIGN KEY (workbook_id) REFERENCES workbooks(id) ON DELETE CASCADE
    )
    """)

    # 用户答题进度记录表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workbook_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        user_answer TEXT,
        is_correct INTEGER DEFAULT 0, -- 1 for correct, 0 for incorrect
        is_starred INTEGER DEFAULT 0, -- 1 for starred, 0 for not
        is_killed INTEGER DEFAULT 0,  -- 1 for killed (熟题斩杀)
        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(workbook_id, question_id),
        FOREIGN KEY (workbook_id) REFERENCES workbooks(id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
    )
    """)

    # 学习时长与每日刷题统计表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        study_date TEXT NOT NULL UNIQUE, -- 'YYYY-MM-DD'
        duration_seconds INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 错题本表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wrong_book (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workbook_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        wrong_count INTEGER DEFAULT 1,
        last_wrong_answer TEXT DEFAULT '',
        is_mastered INTEGER DEFAULT 0, -- 1 if user marked as mastered/removed
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(workbook_id, question_id),
        FOREIGN KEY (workbook_id) REFERENCES workbooks(id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
    )
    """)

    # 笔记表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL UNIQUE,
        content TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
    )
    """)

    # 用户账户表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        nickname TEXT NOT NULL,
        avatar TEXT DEFAULT '',
        role TEXT DEFAULT 'user', -- 'admin' 或 'user'
        is_active INTEGER DEFAULT 1, -- 1 为正常，0 为封禁
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 用户鉴权 Token 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 用户全量云端数据表（实现手机、电脑、多端静默自动无缝同步）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_cloud_data (
        user_id INTEGER PRIMARY KEY,
        records_json TEXT NOT NULL DEFAULT '{}',
        stats_json TEXT NOT NULL DEFAULT '{}',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 全局系统安全配置表（防恶意注册与安全开关）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 初始化默认安全配置
    default_settings = [
        ("allow_registration", "true", "全站是否开放新用户注册(true/false)"),
        ("invite_code_enabled", "true", "是否启用注册邀请码校验(true/false)"),
        ("invite_code", "2027kaoyan", "注册专属邀请口令")
    ]
    for s_key, s_val, s_desc in default_settings:
        cursor.execute("""
            INSERT OR IGNORE INTO system_settings (key, value, description)
            VALUES (?, ?, ?)
        """, (s_key, s_val, s_desc))

    # 检查并补充字段
    cursor.execute("PRAGMA table_info(user_progress)")
    up_cols = [c[1] for c in cursor.fetchall()]
    if "is_killed" not in up_cols:
        cursor.execute("ALTER TABLE user_progress ADD COLUMN is_killed INTEGER DEFAULT 0")

    cursor.execute("PRAGMA table_info(users)")
    user_cols = [c[1] for c in cursor.fetchall()]
    if "role" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    if "is_active" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")

    # 默认将创始用户提升为超级管理员
    cursor.execute("""
        UPDATE users SET role = 'admin' 
        WHERE id = 1 OR username IN ('zjw_student', 'zjw2027', 'admin')
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
