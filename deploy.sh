#!/bin/bash
set -e

echo "=========================================================="
echo " 🚀 开始自动部署：考研政治刷题掌上宝 (PolicyMaster)"
echo " 目标服务器：阿里云 ECS (Ubuntu 24.04)"
echo "=========================================================="

# 1. 禁用交互提示，快速更新与安装系统依赖
export DEBIAN_FRONTEND=noninteractive
echo "[1/5] 安装 Python3、Git 及必要工具..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl

# 2. 准备代码目录
echo "[2/5] 获取最新刷题系统与全量真题库代码..."
mkdir -p /var/www
cd /var/www

if [ -d "policy-study" ]; then
    echo "发现已有目录，正在拉取最新代码..."
    cd policy-study
    git fetch --all
    git reset --hard origin/main
else
    # 优先直连 GitHub，若失败则通过加速代理克隆
    if ! git clone https://github.com/Zjwexercise/policy-study.git; then
        echo "直连较慢，使用高速镜像加速克隆..."
        git clone https://ghfast.top/https://github.com/Zjwexercise/policy-study.git policy-study
    fi
    cd policy-study
fi

# 3. 创建 Python 虚拟环境并安装后端运行库
echo "[3/5] 构建 Python 运行环境与依赖..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
./venv/bin/pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 初始化云端数据库
echo "[4/5] 校验并初始化数据库..."
cd backend
../venv/bin/python database.py
cd ..

# 5. 配置 systemd 后台常驻守护进程（开机自启、崩溃自愈、24小时长盛不衰）
echo "[5/5] 配置系统级 24 小时开机自启守护服务..."
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
