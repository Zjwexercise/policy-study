#!/bin/bash
set -e

echo "=========================================================="
echo " 🚀 正在完成自动部署：考研政治刷题掌上宝 (PolicyMaster)"
echo " 目标服务器：阿里云 ECS"
echo "=========================================================="

# 1. 检查基础环境（如果已安装则直接跳过 apt，避免撞系统自动更新锁）
if ! command -v python3 >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
    echo "[1/4] 安装必要工具..."
    systemctl stop unattended-upgrades 2>/dev/null || true
    killall -9 apt-get apt unattended-upgrades 2>/dev/null || true
    sleep 1
    rm -f /var/lib/dpkg/lock* /var/cache/apt/archives/lock* 2>/dev/null || true
    apt-get update -y || true
    apt-get install -y python3 python3-pip python3-venv git curl || true
else
    echo "[1/4] 检测到 Python3 与 Git 已就绪，直接跳过 apt！"
fi

# 2. 准备代码目录
echo "[2/4] 获取最新题库与项目代码..."
mkdir -p /var/www
cd /var/www

if [ -d "policy-study" ]; then
    echo "发现已有目录，正在更新为最新代码与全量题库数据..."
    cd policy-study
    # 备份保护云端用户的最新做题进度与数据库，防止被覆盖
    if [ -f "backend/policy_study.db" ]; then
        cp -p backend/policy_study.db /var/www/policy_study.db.safe_backup 2>/dev/null || true
    fi
    git remote set-url origin https://ghfast.top/https://github.com/Zjwexercise/policy-study.git 2>/dev/null || true
    git fetch origin main || git fetch --all || true
    git reset --hard origin/main || true
    # 恢复云端实时题库与做题记录数据库
    if [ -f "/var/www/policy_study.db.safe_backup" ]; then
        cp -p /var/www/policy_study.db.safe_backup backend/policy_study.db 2>/dev/null || true
    fi
else
    if ! git clone https://ghfast.top/https://github.com/Zjwexercise/policy-study.git policy-study; then
        echo "镜像拉取失败，尝试直连拉取..."
        git clone https://github.com/Zjwexercise/policy-study.git policy-study
    fi
    cd policy-study
fi

# 3. 创建 Python 虚拟环境并安装依赖
echo "[3/5] 构建 Python 运行环境与依赖..."
rm -rf venv
python3 -m venv venv
./venv/bin/pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com || true
./venv/bin/pip install fastapi uvicorn pydantic python-multipart aiofiles -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
./venv/bin/pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com || true

# 4. 初始化云端数据库
echo "[4/4] 校验并初始化数据库..."
cd /var/www/policy-study/backend
../venv/bin/python database.py
cd /var/www/policy-study

# 5. 清理历史遗留进程并配置 systemd 后台常驻守护进程
echo "[5/5] 清理 8000 端口历史进程并配置 24 小时开机自启守护服务..."
# 杀死可能占用 8000 端口的旧进程（如之前的旧脚本）
fuser -k 8000/tcp 2>/dev/null || true
PID_8000=$(ss -lptn 'sport = :8000' 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2)
if [ -n "$PID_8000" ]; then
    kill -9 $PID_8000 2>/dev/null || true
fi

cat << 'EOF' > /etc/systemd/system/policy-study.service
[Unit]
Description=Policy Study Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/policy-study/backend
ExecStart=/var/www/policy-study/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable policy-study.service
systemctl restart policy-study.service

# 开放系统内部防火墙（如启用了 ufw）
if command -v ufw >/dev/null 2>&1; then
    ufw allow 80/tcp || true
    ufw allow 8000/tcp || true
fi

echo "=========================================================="
echo " 🎉 恭喜！考研政治刷题掌上宝 已成功部署并启动！"
echo " 🌐 访问地址 (手机/电脑均可直接打开)："
echo "    http://47.93.172.13:8000"
echo "=========================================================="
