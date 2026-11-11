#!/bin/bash
set -e

echo "=========================================================="
echo " 🚀 正在极速热更新：考研政治刷题掌上宝 (PolicyMaster)"
echo "=========================================================="

cd /var/www/policy-study

# 1. 备份保护做题数据库
if [ -f "backend/policy_study.db" ]; then
    cp -p backend/policy_study.db /var/www/policy_study.db.safe_backup 2>/dev/null || true
fi

# 2. 从 GitHub 加速镜像拉取最新提交
git remote set-url origin https://ghfast.top/https://github.com/Zjwexercise/policy-study.git 2>/dev/null || true
git fetch origin main || git fetch --all || true
git reset --hard origin/main || true

# 3. 恢复数据库，保证刷题记录完整不丢失
if [ -f "/var/www/policy_study.db.safe_backup" ]; then
    cp -p /var/www/policy_study.db.safe_backup backend/policy_study.db 2>/dev/null || true
fi

# 4. 重启守护服务
systemctl restart policy-study

echo "=========================================================="
echo " 🎉 更新完成！最新前端与后端功能已上线！"
echo " 🌐 访问地址：http://47.93.172.13:8000"
echo "=========================================================="
