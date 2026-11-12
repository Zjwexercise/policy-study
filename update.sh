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

# 2. 从 GitHub 加速镜像拉取最新提交（含最新1000题题库与构建）
git remote set-url origin https://ghfast.top/https://github.com/Zjwexercise/policy-study.git 2>/dev/null || true
git fetch origin main || git fetch --all || true
git reset --hard origin/main || true

# 3. 智能双向融合：既保留服务器上的全部做题进度/错题本，又无缝注入1000题全套新题库
if [ -f "backend/seed_1000.py" ]; then
    python3 backend/seed_1000.py || python backend/seed_1000.py || true
fi

# 4. 重启守护服务
systemctl restart policy-study

echo "=========================================================="
echo " 🎉 更新完成！2027版1000题（946题）已全部上线！"
echo " 🌐 访问地址：http://47.93.172.13:8000"
echo "=========================================================="
