# -*- coding: utf-8 -*-
"""TransFlow-J 机器学习服务（PyCharm 运行入口）。

职责：承载需要「模型」的环节 —— 领域判定、期刊风格翻译、风格判别。
模型尚未接入时，接口返回明确状态而非报错，保证前后端始终可联调。

启动方式（PyCharm 直接运行本文件即可）：
    cd ml
    pip install -r requirements.txt
    运行 app.py          # 等价于 python app.py
    或命令行：uvicorn app:app --host 127.0.0.1 --port 8000

接口一览：
    GET  /health           健康检查
    POST /term/analyze     术语领域判定（译前准备）
    POST /style/translate  期刊风格翻译（成段 / 整篇）
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 仓库根目录：ml/app.py -> ml -> 仓库根
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

app = FastAPI(title="TransFlow-J ML Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load(rel: str):
    """读取 data/ 下的 JSON，不存在返回 None。"""
    p = DATA / rel
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


class TermRequest(BaseModel):
    term: str = ""
    context: str = ""


class StyleRequest(BaseModel):
    journal: str = ""
    text: str = ""
    scope: str = "paragraph"          # paragraph（成段） | full（整篇）
    model: str | None = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "transflow-ml",
        "models_loaded": False,
        "note": "期刊风格模型尚未接入；/style/translate 会返回 model_unavailable",
    }


@app.post("/term/analyze")
def term_analyze(req: TermRequest):
    """术语领域判定：与 Java 侧同规则（关键词打分）。"""
    kw = _load("termbase/domain_keywords.json")
    if not kw:
        return {"term": req.term, "domain": "unknown", "domain_zh": "未识别领域",
                "confidence": 0.0, "matched_keywords": [],
                "reason": "领域关键词表缺失（data/termbase/domain_keywords.json）"}

    hay = f"{req.term} {req.context}".lower()
    best_key = None
    best_zh = None
    best_hits: list[str] = []
    for key, d in kw.get("domains", {}).items():
        hits = [k for k in d.get("keywords", []) if k.lower() in hay]
        if len(hits) > len(best_hits):
            best_key, best_zh, best_hits = key, d.get("domain_zh"), hits

    if not best_key:
        return {"term": req.term, "domain": "unknown", "domain_zh": "未识别领域",
                "confidence": 0.0, "matched_keywords": [],
                "reason": "未命中任何领域关键词，建议补充上下文"}
    conf = round(min(1.0, len(best_hits) / 3.0), 2)
    return {"term": req.term, "domain": best_key, "domain_zh": best_zh,
            "confidence": conf, "matched_keywords": best_hits,
            "reason": f"命中 {len(best_hits)} 个领域关键词"}


@app.post("/style/translate")
def style_translate(req: StyleRequest):
    """期刊风格翻译（成段 / 整篇）。模型未接入时返回明确状态。"""
    if not req.text.strip():
        return {"status": "invalid", "message": "文本为空"}
    # TODO: 接入微调后的期刊风格模型：
    #   路径 A（提示词卡）：按 journal 组装风格约束 + 基座模型
    #   路径 B（LoRA）：加载 ml/models/{journal}/ 下的适配器
    return {
        "status": "model_unavailable",
        "message": "期刊风格模型尚未接入。请在 ml/ 下完成风格模型训练后在此处加载。",
        "journal": req.journal,
        "scope": req.scope,
        "engine": "ml-service(stub)",
        "translation": None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
