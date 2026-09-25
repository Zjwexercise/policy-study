import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db, UPLOAD_DIR
from seed_data import seed_default_workbook
from routers.workbooks import router as workbooks_router
from routers.questions import router as questions_router
from routers.practice import router as practice_router
from routers.wrong_book import router as wrong_book_router
from routers.notes import router as notes_router
from routers.system import router as system_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库与示范数据
    init_db()
    seed_default_workbook()
    yield

app = FastAPI(
    title="考研政治刷题掌上宝 API",
    description="支持 PDF 题目解析、单选多选即时刷题、错题本、考点笔记、二刷重置等功能",
    version="1.0.0",
    lifespan=lifespan
)

# 允许跨域（支持前端 Vite 开发服务器）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(workbooks_router)
app.include_router(questions_router)
app.include_router(practice_router)
app.include_router(wrong_book_router)
app.include_router(notes_router)
app.include_router(system_router)

# 挂载上传文件目录
if os.path.exists(UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 挂载前端构建产物（若存在 dist 目录）
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(target) and os.path.isfile(target):
            return FileResponse(target)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def index():
        return {
            "status": "running",
            "message": "考研政治刷题掌上宝后端运行中。前端开发模式请访问 http://localhost:5173"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
