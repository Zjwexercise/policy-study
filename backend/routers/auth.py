import hashlib
import secrets
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field

from database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 内存级 IP 注册限流字典：ip -> [timestamp, ...]
_ip_register_records: Dict[str, List[datetime]] = {}

def check_ip_rate_limit(client_ip: str, max_requests: int = 3, window_seconds: int = 60):
    """防脚本爆破与批量恶意注册：限制同 IP 在指定时间内最多注册次数"""
    now = datetime.now()
    cutoff = now - timedelta(seconds=window_seconds)
    
    # 清理过期记录
    timestamps = [t for t in _ip_register_records.get(client_ip, []) if t > cutoff]
    if len(timestamps) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"注册请求过于频繁，为防止机器人恶意灌水，请 {window_seconds} 秒后再试。"
        )
    timestamps.append(now)
    _ip_register_records[client_ip] = timestamps

def hash_password(password: str, salt: str) -> str:
    """使用 PBKDF2-HMAC-SHA256 进行密码哈希，具备高强度防暴力破解"""
    return hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    ).hex()

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    return secrets.compare_digest(hash_password(password, salt), expected_hash)

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=32, description="登录账号（支持11位手机号或英文数字账号）")
    phone: Optional[str] = Field(None, max_length=20, description="手机号码（选填）")
    password: str = Field(..., min_length=4, max_length=64, description="登录密码")
    nickname: Optional[str] = Field(None, max_length=32, description="用户昵称")
    invite_code: Optional[str] = Field(None, max_length=64, description="注册专属邀请口令")

class LoginRequest(BaseModel):
    username: str = Field(..., description="登录账号（支持用户名或11位手机号）")
    password: str = Field(..., description="登录密码")

class SyncRequest(BaseModel):
    client_records: Dict[str, Any] = Field(default_factory=dict, description="客户端新增或更新的做题记录")
    client_stats: Dict[str, Any] = Field(default_factory=dict, description="客户端学习时长与做题统计")

def get_current_user_from_header(
    authorization: Optional[str] = Header(None),
    conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供身份认证凭据，请先登录")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=401, detail="认证凭据格式不正确")
    
    token = parts[1]
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.phone, u.nickname, u.avatar, u.role, u.is_active, u.created_at
        FROM user_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token = ?
    """, (token,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="登录凭据已过期或无效，请重新登录")
    
    if row["is_active"] == 0:
        raise HTTPException(status_code=403, detail="该账号已被管理员封禁，无法使用系统服务")
    
    return {
        "id": row["id"],
        "username": row["username"],
        "phone": row["phone"] or "",
        "nickname": row["nickname"],
        "avatar": row["avatar"],
        "role": row["role"] or "user",
        "is_active": row["is_active"],
        "created_at": row["created_at"]
    }

def get_current_admin(
    current_user: dict = Depends(get_current_user_from_header)
) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="无权访问管理员后台，需要超级管理员权限")
    return current_user

@router.get("/register-config")
def get_register_config(conn: sqlite3.Connection = Depends(get_db)):
    """获取公开的注册安全策略配置"""
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM system_settings WHERE key IN ('allow_registration', 'invite_code_enabled')")
    settings = dict(cursor.fetchall())
    return {
        "allow_registration": settings.get("allow_registration", "true").lower() == "true",
        "invite_code_required": settings.get("invite_code_enabled", "true").lower() == "true"
    }

@router.post("/register")
def register(
    req: RegisterRequest, 
    request: Request,
    conn: sqlite3.Connection = Depends(get_db)
):
    # 1. 检查 IP 注册频率（防脚本刷爆）
    client_ip = request.client.host if request.client else "127.0.0.1"
    check_ip_rate_limit(client_ip)

    cursor = conn.cursor()

    # 2. 检查系统注册开关与邀请码
    cursor.execute("SELECT key, value FROM system_settings")
    settings = dict(cursor.fetchall())

    if settings.get("allow_registration", "true").lower() != "true":
        raise HTTPException(status_code=403, detail="系统当前已暂停新用户公开注册，请联系管理员")

    if settings.get("invite_code_enabled", "true").lower() == "true":
        expected_code = settings.get("invite_code", "2027kaoyan").strip()
        user_code = (req.invite_code or "").strip()
        if not user_code or user_code != expected_code:
            raise HTTPException(status_code=400, detail="注册邀请口令不正确，防恶意灌水保护已拦截")

    username = req.username.strip()
    if len(username) < 2:
        raise HTTPException(status_code=400, detail="用户名或手机号不能少于2个字符")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="密码长度不能少于4位")
    
    phone = (req.phone or "").strip()
    # 自动识别 11 位手机号码（以 1 开头的 11 位纯数字）
    import re
    if re.match(r"^1[3-9]\d{9}$", username):
        if not phone:
            phone = username

    nickname = (req.nickname or "").strip() or username

    # 检查用户名或手机号是否已存在
    if phone:
        cursor.execute("SELECT id FROM users WHERE username = ? OR (phone != '' AND phone = ?)", (username, phone))
    else:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="该账号或手机号已被注册，请直接登录或换一个号码")

    salt = secrets.token_hex(16)
    pwd_hash = hash_password(req.password, salt)

    cursor.execute("""
        INSERT INTO users (username, phone, password_hash, salt, nickname, role, is_active)
        VALUES (?, ?, ?, ?, ?, 'user', 1)
    """, (username, phone, pwd_hash, salt, nickname))
    user_id = cursor.lastrowid

    # 初始化该用户的云端存档
    cursor.execute("""
        INSERT INTO user_cloud_data (user_id, records_json, stats_json)
        VALUES (?, '{}', '{}')
    """, (user_id,))

    # 生成长期有效 Token
    token = secrets.token_urlsafe(32)
    cursor.execute("""
        INSERT INTO user_tokens (token, user_id)
        VALUES (?, ?)
    """, (token, user_id))

    conn.commit()

    return {
        "success": True,
        "message": "注册成功",
        "token": token,
        "user": {
            "id": user_id,
            "username": username,
            "phone": phone,
            "nickname": nickname,
            "role": "user"
        },
        "cloud_data": {
            "records": {},
            "stats": {}
        }
    }

@router.post("/login")
def login(req: LoginRequest, conn: sqlite3.Connection = Depends(get_db)):
    account = req.username.strip()
    cursor = conn.cursor()
    # 支持用户名或手机号双重免切换直接登录
    cursor.execute("""
        SELECT id, username, phone, password_hash, salt, nickname, avatar, role, is_active
        FROM users 
        WHERE username = ? OR (phone != '' AND phone = ?)
    """, (account, account))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="账号或密码不正确")

    if not verify_password(req.password, row["salt"], row["password_hash"]):
        raise HTTPException(status_code=400, detail="账号或密码不正确")

    if row["is_active"] == 0:
        raise HTTPException(status_code=403, detail="该账号已被管理员封禁，无法登录系统")

    user_id = row["id"]
    # 更新最后登录时间
    cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))

    # 获取或生成 Token
    token = secrets.token_urlsafe(32)
    cursor.execute("INSERT INTO user_tokens (token, user_id) VALUES (?, ?)", (token, user_id))

    # 获取该用户的全部云端数据
    cursor.execute("SELECT records_json, stats_json FROM user_cloud_data WHERE user_id = ?", (user_id,))
    cdata = cursor.fetchone()
    records = {}
    stats = {}
    if cdata:
        try:
            records = json.loads(cdata["records_json"])
        except Exception:
            records = {}
        try:
            stats = json.loads(cdata["stats_json"])
        except Exception:
            stats = {}

    conn.commit()

    return {
        "success": True,
        "message": "登录成功",
        "token": token,
        "user": {
            "id": user_id,
            "username": row["username"],
            "phone": row["phone"] or "",
            "nickname": row["nickname"],
            "avatar": row["avatar"],
            "role": row["role"] or "user"
        },
        "cloud_data": {
            "records": records,
            "stats": stats
        }
    }

@router.get("/me")
def get_current_user_profile(
    current_user: dict = Depends(get_current_user_from_header),
    conn: sqlite3.Connection = Depends(get_db)
):
    cursor = conn.cursor()
    cursor.execute("SELECT updated_at FROM user_cloud_data WHERE user_id = ?", (current_user["id"],))
    row = cursor.fetchone()
    last_sync = row["updated_at"] if row else None

    return {
        "success": True,
        "user": current_user,
        "last_sync": last_sync
    }

@router.post("/sync")
def sync_records(
    req: SyncRequest,
    current_user: dict = Depends(get_current_user_from_header),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    智能云端双向同步：
    将客户端本次上传的记录与云端记录合并（增量智能合并），
    并返回最新合并后的全量数据给客户端。
    """
    user_id = current_user["id"]
    cursor = conn.cursor()

    cursor.execute("SELECT records_json, stats_json FROM user_cloud_data WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    server_records = {}
    server_stats = {}
    if row:
        try:
            server_records = json.loads(row["records_json"])
        except Exception:
            server_records = {}
        try:
            server_stats = json.loads(row["stats_json"])
        except Exception:
            server_stats = {}

    # 智能合并算法
    client_rec = req.client_records or {}
    for k, in_val in client_rec.items():
        if not k.startswith("policy_"):
            continue
        s_val = server_records.get(k)

        if k.startswith("policy_ans_"):
            if s_val is None:
                server_records[k] = in_val
            else:
                qid = k.split("_")[3]
                s_cor = server_records.get(f"policy_cor_{qid}")
                in_cor = client_rec.get(f"policy_cor_{qid}")
                if in_cor == "1" and s_cor != "1":
                    server_records[k] = in_val
                    server_records[f"policy_cor_{qid}"] = "1"
        elif k.startswith("policy_cor_"):
            if s_val is None or (in_val == "1" and s_val != "1"):
                server_records[k] = in_val
        elif k.startswith("policy_wrong_cnt_"):
            s_num = int(s_val or 0)
            in_num = int(in_val or 0)
            server_records[k] = str(max(s_num, in_num))
        elif k.startswith("policy_wrong_master_"):
            if s_val is None or in_val == "1":
                server_records[k] = in_val
        elif k.startswith("policy_killed_") and not k.startswith("policy_killed_at_"):
            if s_val is None or in_val == "1":
                server_records[k] = in_val
        elif k.startswith("policy_killed_at_"):
            if s_val is None:
                server_records[k] = in_val
            elif in_val:
                try:
                    t_s = datetime.fromisoformat(str(s_val))
                    t_in = datetime.fromisoformat(str(in_val))
                    if t_in > t_s:
                        server_records[k] = in_val
                except Exception:
                    server_records[k] = in_val
        elif k.startswith("policy_star_"):
            if s_val is None or in_val == "1":
                server_records[k] = in_val
        elif k.startswith("policy_note_"):
            s_str = str(s_val or "").strip()
            in_str = str(in_val or "").strip()
            if not s_str:
                if in_str:
                    server_records[k] = in_str
            elif in_str and s_str != in_str:
                if in_str not in s_str:
                    server_records[k] = f"{s_str}\n\n[云端合并笔记]:\n{in_str}"
        else:
            if s_val is None:
                server_records[k] = in_val

    # 合并学习时长与每日刷题数统计（兼容时长秒数字值与复杂字典）
    client_stats = req.client_stats or {}
    for date_key, in_stat in client_stats.items():
        if date_key not in server_stats:
            server_stats[date_key] = in_stat
        else:
            if isinstance(server_stats[date_key], dict) and isinstance(in_stat, dict):
                s_sec = server_stats[date_key].get("duration_seconds", 0)
                in_sec = in_stat.get("duration_seconds", 0)
                server_stats[date_key]["duration_seconds"] = max(s_sec, in_sec)
                s_cnt = server_stats[date_key].get("question_count", 0)
                in_cnt = in_stat.get("question_count", 0)
                server_stats[date_key]["question_count"] = max(s_cnt, in_cnt)
            else:
                try:
                    s_num = int(server_stats[date_key] or 0)
                except Exception:
                    s_num = 0
                try:
                    in_num = int(in_stat or 0)
                except Exception:
                    in_num = 0
                server_stats[date_key] = max(s_num, in_num)

    # 保存最新合并数据
    now_str = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO user_cloud_data (user_id, records_json, stats_json, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            records_json = excluded.records_json,
            stats_json = excluded.stats_json,
            updated_at = excluded.updated_at
    """, (user_id, json.dumps(server_records, ensure_ascii=False), json.dumps(server_stats, ensure_ascii=False), now_str))

    conn.commit()

    return {
        "success": True,
        "message": "云端同步完成",
        "updated_at": now_str,
        "merged_records": server_records,
        "server_records": server_records,
        "merged_stats": server_stats,
        "server_stats": server_stats
    }

@router.post("/logout")
def logout(
    authorization: Optional[str] = Header(None),
    conn: sqlite3.Connection = Depends(get_db)
):
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_tokens WHERE token = ?", (token,))
            conn.commit()
    return {"success": True, "message": "已成功退出登录"}
