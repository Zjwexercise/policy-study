FROM python:3.10-slim

WORKDIR /app

# 安装必要的系统工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# 复制完整的后端（包含 policy_study.db 完整 1500+ 题库）
COPY backend ./backend

# 复制已编译好的前端静态文件
COPY frontend/dist ./frontend/dist

# 暴露端口（平台通常会自动注入 PORT 环境变量）
ENV PORT=8000
EXPOSE 8000

# 启动 FastAPI 服务，同时支持环境变量中的 PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir /app/backend"]
