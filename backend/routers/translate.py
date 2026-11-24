import sqlite3
import json
import hashlib
import urllib.request
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from database import get_db

router = APIRouter(prefix="/api/translate", tags=["translate"])

# 确保翻译缓存表存在
def init_translations_table(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS translations (
        hash TEXT PRIMARY KEY,
        source_lang TEXT DEFAULT 'zh',
        target_lang TEXT DEFAULT 'th',
        source_text TEXT NOT NULL,
        translated_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_hash ON translations(hash)")
    conn.commit()

class TranslateTextRequest(BaseModel):
    text: str
    target_lang: str = "th"
    source_lang: str = "zh"

class TranslateQuestionRequest(BaseModel):
    question_id: Optional[int] = None
    stem: str
    options: Optional[List[Dict[str, str]]] = None # [{"key": "A", "value": "..."}, ...]
    explanation: Optional[str] = None
    target_lang: str = "th"

def _calc_hash(text: str, target_lang: str) -> str:
    clean = (text or "").strip()
    return hashlib.md5(f"{clean}_{target_lang}".encode("utf-8")).hexdigest()

def _fetch_mymemory(text: str, target_lang: str = "th", source_lang: str = "zh-CN") -> str:
    if not text or not text.strip():
        return ""
    
    clean_text = text.strip()
    # MyMemory API 允许单次请求 500 字符内，对于超长解析进行切分请求
    if len(clean_text) <= 450:
        encoded = urllib.parse.quote(clean_text)
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair={source_lang}|{target_lang}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            res_text = data.get("responseData", {}).get("translatedText") or ""
            return res_text
    else:
        # 长文本按标点拆分翻译后合并
        parts = []
        current = ""
        for char in clean_text:
            current += char
            if char in ("。", "\n", "；") and len(current) >= 150:
                parts.append(current)
                current = ""
        if current:
            parts.append(current)
        
        translated_parts = []
        for p in parts:
            try:
                translated_parts.append(_fetch_mymemory(p, target_lang, source_lang))
            except Exception:
                translated_parts.append(p)
        return "".join(translated_parts)

@router.post("")
def translate_single_text(req: TranslateTextRequest, conn: sqlite3.Connection = Depends(get_db)):
    init_translations_table(conn)
    cursor = conn.cursor()
    
    h = _calc_hash(req.text, req.target_lang)
    cursor.execute("SELECT translated_text FROM translations WHERE hash = ?", (h,))
    row = cursor.fetchone()
    if row and row["translated_text"]:
        return {"translated_text": row["translated_text"], "cached": True}
    
    try:
        translated = _fetch_mymemory(req.text, target_lang=req.target_lang)
        if translated:
            cursor.execute(
                "INSERT OR REPLACE INTO translations (hash, source_lang, target_lang, source_text, translated_text) VALUES (?, ?, ?, ?, ?)",
                (h, req.source_lang, req.target_lang, req.text, translated)
            )
            conn.commit()
        return {"translated_text": translated, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译服务连接异常: {str(e)}")

@router.post("/question")
def translate_question_bundle(req: TranslateQuestionRequest, conn: sqlite3.Connection = Depends(get_db)):
    init_translations_table(conn)
    cursor = conn.cursor()

    result = {
        "stem": "",
        "options": {},
        "explanation": ""
    }

    # 1. 题干翻译
    if req.stem:
        stem_hash = _calc_hash(req.stem, req.target_lang)
        cursor.execute("SELECT translated_text FROM translations WHERE hash = ?", (stem_hash,))
        row = cursor.fetchone()
        if row and row["translated_text"]:
            result["stem"] = row["translated_text"]
        else:
            try:
                trans_stem = _fetch_mymemory(req.stem, target_lang=req.target_lang)
                if trans_stem:
                    cursor.execute(
                        "INSERT OR REPLACE INTO translations (hash, source_lang, target_lang, source_text, translated_text) VALUES (?, ?, ?, ?, ?)",
                        (stem_hash, "zh", req.target_lang, req.stem, trans_stem)
                    )
                    result["stem"] = trans_stem
            except Exception as e:
                result["stem"] = req.stem

    # 2. 选项翻译
    if req.options:
        for opt in req.options:
            key = opt.get("key", "")
            val = opt.get("value", "")
            if not val:
                continue
            opt_hash = _calc_hash(val, req.target_lang)
            cursor.execute("SELECT translated_text FROM translations WHERE hash = ?", (opt_hash,))
            row = cursor.fetchone()
            if row and row["translated_text"]:
                result["options"][key] = row["translated_text"]
            else:
                try:
                    trans_val = _fetch_mymemory(val, target_lang=req.target_lang)
                    if trans_val:
                        cursor.execute(
                            "INSERT OR REPLACE INTO translations (hash, source_lang, target_lang, source_text, translated_text) VALUES (?, ?, ?, ?, ?)",
                            (opt_hash, "zh", req.target_lang, val, trans_val)
                        )
                        result["options"][key] = trans_val
                except Exception:
                    result["options"][key] = val

    # 3. 解析翻译
    if req.explanation:
        exp_hash = _calc_hash(req.explanation, req.target_lang)
        cursor.execute("SELECT translated_text FROM translations WHERE hash = ?", (exp_hash,))
        row = cursor.fetchone()
        if row and row["translated_text"]:
            result["explanation"] = row["translated_text"]
        else:
            try:
                trans_exp = _fetch_mymemory(req.explanation, target_lang=req.target_lang)
                if trans_exp:
                    cursor.execute(
                        "INSERT OR REPLACE INTO translations (hash, source_lang, target_lang, source_text, translated_text) VALUES (?, ?, ?, ?, ?)",
                        (exp_hash, "zh", req.target_lang, req.explanation, trans_exp)
                    )
                    result["explanation"] = trans_exp
            except Exception:
                result["explanation"] = req.explanation

    conn.commit()
    return result
