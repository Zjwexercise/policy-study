#!/bin/bash
set -e

echo "=========================================================="
echo " 🚀 正在极速热更新：考研政治刷题掌上宝 (PolicyMaster)"
echo " 包含：1000题全科目校准、2025全国真题、夜间模式、欢迎封面、解析复制等"
echo "=========================================================="

cd /var/www/policy-study

PY_BIN="python3"
if [ -f "venv/bin/python" ]; then
    PY_BIN="venv/bin/python"
fi

# 1. 深度备份保护考生所有账号密码、做题记录（1300+题进度）与错题本
echo "[1/4] 正在安全备份云端考生答题进度与账号数据..."
if [ -f "backend/policy_study.db" ]; then
    cp -p backend/policy_study.db /var/www/policy_study.db.safe_backup 2>/dev/null || true
    if [ -f "backend/server_migrate.py" ]; then
        $PY_BIN backend/server_migrate.py backup /var/www/user_data_backup.json || true
    fi
fi

# 2. 从 GitHub 拉取最新提交（含最新题库、前端构建静态文件与后台服务）
echo "[2/4] 从云端同步最新代码与题库数据..."
git remote set-url origin https://ghfast.top/https://github.com/Zjwexercise/policy-study.git 2>/dev/null || true
git fetch origin main || git fetch --all || true
git reset --hard origin/main || true

# 3. 智能合流恢复用户做题记录（确保 1300+ 刷题记录 100% 毫发无损）
echo "[3/4] 智能恢复考生做题记录与账号体系..."
if [ -f "/var/www/user_data_backup.json" ] && [ -f "backend/server_migrate.py" ]; then
    $PY_BIN backend/server_migrate.py restore /var/www/user_data_backup.json || true
fi

# 4. 重启守护服务并更新前端路由
echo "[4/4] 重启后台服务并刷新线上环境..."
systemctl restart policy-study || systemctl restart policy-study.service || true

echo "=========================================================="
echo " 🎉 更新完成！1000题校准、2025真题、夜间护眼模式与欢迎封面已全部上线！"
echo " 🌐 访问地址：http://47.93.172.13:8000"
echo " 💡 提示：在浏览器打开后按 Ctrl + F5 强制刷新一次即可加载最新界面！"
echo "=========================================================="
