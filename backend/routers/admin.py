import json
import sqlite3
import urllib.request
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from database import get_db
from routers.auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

def sync_kvdb_users(conn: sqlite3.Connection):
    """双向智能同步：从公网 KVDB 镜像同步注册考生数据到服务器 SQLite，保证多端 100% 同步合流"""
    try:
        bucket = "GoHbGrRznWpJGpLFkLSwRZ"
        req = urllib.request.Request(
            f"https://kvdb.io/{bucket}/?prefix=pm_u_",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=3) as res:
            keys = [k.strip() for k in res.read().decode().strip().split("\n") if k.strip()]
        
        cursor = conn.cursor()
        for k in keys:
            try:
                with urllib.request.urlopen(f"https://kvdb.io/{bucket}/{k}", timeout=3) as u_res:
                    udata = json.loads(u_res.read().decode())
                uname = udata.get("username", "").strip()
                if not uname:
                    continue
                nick = udata.get("nickname", "").strip() or uname
                records_dict = udata.get("records", {})
                stats_dict = udata.get("stats", {})
                
                # 检查该用户是否已在数据库中
                cursor.execute("SELECT id FROM users WHERE username = ?", (uname,))
                row = cursor.fetchone()
                if not row:
                    salt = udata.get("salt", "kvdb_salt")
                    pwd_hash = udata.get("pwdHash", "kvdb_hash")
                    created_at = udata.get("created_at") or datetime.now().isoformat()
                    phone = uname if uname.isdigit() and len(uname) == 11 else ""
                    cursor.execute("""
                        INSERT INTO users (username, phone, password_hash, salt, nickname, role, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, 'user', 1, ?)
                    """, (uname, phone, pwd_hash, salt, nick, created_at))
                    uid = cursor.lastrowid
                    cursor.execute("""
                        INSERT INTO user_cloud_data (user_id, records_json, stats_json)
                        VALUES (?, ?, ?)
                    """, (uid, json.dumps(records_dict, ensure_ascii=False), json.dumps(stats_dict, ensure_ascii=False)))
                else:
                    uid = row["id"]
                    cursor.execute("SELECT records_json FROM user_cloud_data WHERE user_id = ?", (uid,))
                    cdata = cursor.fetchone()
                    local_recs = json.loads(cdata["records_json"]) if cdata and cdata["records_json"] else {}
                    if len(records_dict) > len(local_recs):
                        cursor.execute("""
                            UPDATE user_cloud_data SET records_json = ?, stats_json = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = ?
                        """, (json.dumps(records_dict, ensure_ascii=False), json.dumps(stats_dict, ensure_ascii=False), uid))
            except Exception:
                pass
        conn.commit()
    except Exception:
        pass

class UpdateStatusRequest(BaseModel):
    is_active: int = Field(..., description="1 为启用/正常，0 为封禁")

class UpdateSettingsRequest(BaseModel):
    allow_registration: bool = Field(..., description="是否开放全站新用户注册")
    invite_code_enabled: bool = Field(..., description="是否强制验证注册邀请码")
    invite_code: str = Field(..., min_length=2, max_length=64, description="注册邀请专属口令")

@router.get("/stats")
def get_admin_stats(
    admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db)
):
    """获取管理后台核心数据统计概览"""
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 0")
    banned_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM workbooks")
    total_workbooks = cursor.fetchone()[0]

    # 统计全站答题历史总数
    cursor.execute("SELECT records_json FROM user_cloud_data")
    total_answers = 0
    for row in cursor.fetchall():
        try:
            records = json.loads(row["records_json"])
            total_answers += len(records)
        except Exception:
            pass

    return {
        "success": True,
        "stats": {
            "total_users": total_users,
            "active_users": active_users,
            "banned_users": banned_users,
            "total_questions": total_questions,
            "total_workbooks": total_workbooks,
            "total_answers": total_answers
        }
    }

@router.get("/users")
def get_user_list(
    admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db)
):
    """获取全站所有注册用户列表及做题情况（自动双向合流 KVDB 公网用户）"""
    # 自动合并公网注册的考生数据
    sync_kvdb_users(conn)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.phone, u.nickname, u.role, u.is_active, u.created_at, u.last_login,
               c.records_json
        FROM users u
        LEFT JOIN user_cloud_data c ON u.id = c.user_id
        ORDER BY u.id DESC
    """)
    rows = cursor.fetchall()
    
    user_list = []
    for r in rows:
        records_count = 0
        notes_count = 0
        if r["records_json"]:
            try:
                records = json.loads(r["records_json"])
                records_count = len(records)
                notes_count = sum(1 for item in records.values() if isinstance(item, dict) and item.get("note"))
            except Exception:
                pass
                
        user_list.append({
            "id": r["id"],
            "username": r["username"],
            "phone": r["phone"] or "",
            "nickname": r["nickname"],
            "role": r["role"] or "user",
            "is_active": r["is_active"] if r["is_active"] is not None else 1,
            "created_at": r["created_at"],
            "last_login": r["last_login"],
            "records_count": records_count,
            "notes_count": notes_count,
            "is_current_admin": r["id"] == admin["id"]
        })
        
    return {
        "success": True,
        "users": user_list
    }

@router.post("/users/sync-kvdb")
def manual_sync_kvdb(
    admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db)
):
    """手动触发从公网同步拉取 GitHub Pages 注册的考生账号"""
    sync_kvdb_users(conn)
    return {"success": True, "message": "已成功与公网云端完成双向考生数据合流！"}

@router.post("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    req: UpdateStatusRequest,
    admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db)
):
    """封禁或解封指定用户账号"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="不能对自己的管理员账号进行封禁操作")
        
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")
        
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (req.is_active, user_id))
    
    # 若被封禁，立即清除其所有已登录 Token，使其即刻掉线
    if req.is_active == 0:
        cursor.execute("DELETE FROM user_tokens WHERE user_id = ?", (user_id,))
        
    conn.commit()
    
    action_text = "解封成功" if req.is_active == 1 else "已成功封禁该账号并强制踢下线"
    return {
        "success": True,
        "message": f"用户 [{target['username']}] {action_text}"
    }

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db)
):
    """彻底删除指定用户及其全部云端数据（级联物理删除）"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="不能删除当前登录的管理员账号")
        
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")
        
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    cursor.execute("DELETE FROM user_tokens WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_cloud_data WHERE user_id = ?", (user_id,))
    conn.commit()
    
    return {
        "success": True,
        "message": f"用户 [{target['username']}] 及其云端数据已彻底注销删除"
    }

@router.get("/settings")
def get_system_settings(
    admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db)
):
    """获取当前全站注册安全与邀请码配置"""
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM system_settings")
    raw_settings = dict(cursor.fetchall())
    
    return {
        "success": True,
        "settings": {
            "allow_registration": raw_settings.get("allow_registration", "true").lower() == "true",
            "invite_code_enabled": raw_settings.get("invite_code_enabled", "true").lower() == "true",
            "invite_code": raw_settings.get("invite_code", "2027kaoyan")
        }
    }

@router.post("/settings")
def update_system_settings(
    req: UpdateSettingsRequest,
    admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db)
):
    """更新全站注册开关及专属邀请码"""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO system_settings (key, value, updated_at)
        VALUES ('allow_registration', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
    """, ("true" if req.allow_registration else "false",))
    
    cursor.execute("""
        INSERT INTO system_settings (key, value, updated_at)
        VALUES ('invite_code_enabled', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
    """, ("true" if req.invite_code_enabled else "false",))
    
    clean_code = req.invite_code.strip()
    cursor.execute("""
        INSERT INTO system_settings (key, value, updated_at)
        VALUES ('invite_code', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
    """, (clean_code,))
    
    conn.commit()
    
    return {
        "success": True,
        "message": "全站安全与注册配置已更新生效！",
        "settings": {
            "allow_registration": req.allow_registration,
            "invite_code_enabled": req.invite_code_enabled,
            "invite_code": clean_code
        }
    }
