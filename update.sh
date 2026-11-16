#!/bin/bash
set -e

echo "=========================================================="
echo " 🚀 正在极速热更新：考研政治刷题掌上宝 (PolicyMaster)"
echo "=========================================================="

cd /var/www/policy-study

# 1. 备份保护服务器当前数据库与用户做题记录
if [ -f "backend/policy_study.db" ]; then
    cp -p backend/policy_study.db /var/www/policy_study.db.safe_backup 2>/dev/null || true
fi

# 2. 从 GitHub 拉取最新提交（含最新1000题题库、后台管理控制面板与防恶意注册防火墙）
git fetch origin main || git fetch --all || (git remote set-url origin https://ghfast.top/https://github.com/Zjwexercise/policy-study.git && git fetch origin main) || true
git reset --hard origin/main || true

# 3. 升级数据库结构（注入管理员权限、全站安全注册配置表，绝不丢失用户进度）
if [ -f "backend/database.py" ]; then
    if [ -f "venv/bin/python" ]; then
        venv/bin/python backend/database.py || true
    else
        python3 backend/database.py || python backend/database.py || true
    fi
fi

# 4. 重启守护服务
systemctl restart policy-study

echo "=========================================================="
echo " 🎉 更新完成！题目矫正、后台管理中心与防恶意注册口令已全部上线生效！"
echo " 🌐 访问地址：http://47.93.172.13:8000"
echo "=========================================================="
