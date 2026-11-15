import json
import sqlite3
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from database import get_db
from routers.auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

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
    """获取全站所有注册用户列表及做题情况"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.nickname, u.role, u.is_active, u.created_at, u.last_login,
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
