#!/bin/bash
# =========================================================
# 考研政治刷题掌上宝 (PolicyMaster) - 云服务器一键部署脚本
# 适用系统：Ubuntu / Debian / CentOS / Alibaba Cloud Linux / TencentOS
# =========================================================

echo "========================================================="
echo " 🎓 正在为考研政治刷题掌上宝配置云端运行环境..."
echo "========================================================="

# 1. 检查或安装 Docker 与 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "[1/3] 检测到未安装 Docker，正在自动安装 Docker..."
    curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
    systemctl enable --now docker
else
    echo "[1/3] Docker 环境正常！"
fi

if ! command -v docker compose &> /dev/null; then
    echo "[2/3] 安装 Docker Compose 插件..."
    apt-get update && apt-get install -y docker-compose-plugin 2>/dev/null || yum install -y docker-compose-plugin 2>/dev/null
fi

# 2. 构建并启动容器
echo "[3/3] 正在启动考研政治题库云端容器..."
docker compose down 2>/dev/null
docker compose up -d --build

SERVER_IP=$(curl -s ip.sb || curl -s ifconfig.me)

echo ""
echo "========================================================="
echo " 🎉 云端部署成功！服务已在后台 7x24 小时保持运行"
echo "========================================================="
echo " 📱 手机/电脑直接在任何地方访问："
echo "     👉 http://${SERVER_IP}:8000"
echo ""
echo " 💡 温馨提醒："
echo "    请确保在云服务器控制台（安全组/防火墙）中开放 8000 端口！"
echo "========================================================="
