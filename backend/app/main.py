"""
FastAPI 应用入口
学术中译英质量保障平台 - 后端服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import create_tables
from app.api.projects import router as projects_router
from app.api.documents import router as documents_router
from app.api.translation import router as translation_router
from app.api.terminology import router as terminology_router
from app.api.other import (
    journals_router,
    models_router,
    proofreading_router,
    reports_router,
)
from app.api.export import router as export_router

# ============================================================
# 应用初始化
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## 学术中译英质量保障平台

面向中文学术论文的中译英、期刊风格适配、权威术语查证和多模型质量校对平台。

### 核心功能
- 📄 **论文工作台** - 上传 PDF/DOCX，自动分段编号
- 📚 **术语查证** - 按信源等级记录权威证据
- 🌐 **期刊适配** - 注入目标期刊风格约束
- 🤖 **AI 翻译** - 多模型中译英，支持 OpenAI / DeepSeek / Claude 等
- 🔍 **MQM 校对** - 跨厂商独立模型评审，结构化错误报告
- 📊 **质量报告** - 数字一致性、术语一致率、人工采纳率等指标
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================
# CORS 跨域配置（允许前端调用）
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 注册所有路由（统一 /api/v1 前缀）
# ============================================================

PREFIX = "/api/v1"

app.include_router(projects_router, prefix=PREFIX)
app.include_router(documents_router, prefix=PREFIX)
app.include_router(translation_router, prefix=PREFIX)
app.include_router(terminology_router, prefix=PREFIX)
app.include_router(journals_router, prefix=PREFIX)
app.include_router(models_router, prefix=PREFIX)
app.include_router(proofreading_router, prefix=PREFIX)
app.include_router(reports_router, prefix=PREFIX)
app.include_router(export_router, prefix=PREFIX)

# ============================================================
# 生命周期事件
# ============================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.projects_dir, exist_ok=True)
    create_tables()
    print(f"✅ {settings.app_name} v{settings.app_version} 启动成功")
    print(f"📖 API 文档: http://127.0.0.1:8000/docs")


# ============================================================
# 健康检查端点
# ============================================================

@app.get("/", tags=["系统"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok"}
