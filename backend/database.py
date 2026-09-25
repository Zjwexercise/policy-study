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
        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(workbook_id, question_id),
        FOREIGN KEY (workbook_id) REFERENCES workbooks(id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
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

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
