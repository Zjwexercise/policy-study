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
    echo "发现已有目录，正在更新为最新代码..."
    cd policy-study
    git fetch --all || true
    git reset --hard origin/main || true
else
    if ! git clone https://github.com/Zjwexercise/policy-study.git; then
        echo "直连较慢，使用高速镜像加速克隆..."
        git clone https://ghfast.top/https://github.com/Zjwexercise/policy-study.git policy-study
    fi
    cd policy-study
fi

# 3. 创建 Python 虚拟环境并安装依赖
echo "[3/4] 构建 Python 运行环境与依赖..."
rm -rf venv
python3 -m venv venv
./venv/bin/pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com || true
./venv/bin/pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 4. 初始化云端数据库
echo "[4/4] 校验并初始化数据库..."
cd /var/www/policy-study/backend
../venv/bin/python database.py
cd /var/www/policy-study

# 5. 配置 systemd 后台常驻守护进程
echo "配置系统级 24 小时开机自启守护服务..."
cat << 'EOF' > /etc/systemd/system/policy-study.service
[Unit]
Description=Policy Study Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/policy-study/backend
ExecStart=/var/www/policy-study/venv/bin/uvicorn main:app --host 0.0.0.0 --port 80
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable policy-study.service
systemctl restart policy-study.service

# 开放系统防火墙 80 端口（如启用了 ufw）
if command -v ufw >/dev/null 2>&1; then
    ufw allow 80/tcp || true
fi

echo "=========================================================="
echo " 🎉 恭喜！考研政治刷题掌上宝 已成功部署并启动！"
echo " 🌐 访问地址 (手机/电脑均可直接打开)："
echo "    http://47.93.172.13"
echo "=========================================================="
