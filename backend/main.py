"""股票分析 - FastAPI 后端 (含前端页面)"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import API_PREFIX

# 注入 skills 目录
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")
sys.path.insert(0, SKILLS_DIR)

from routers import stock, market

app = FastAPI(title="A股分析", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# API 路由
app.include_router(stock.router, prefix=API_PREFIX, tags=["个股"])
app.include_router(market.router, prefix=API_PREFIX, tags=["市场"])

# 前端页面 —— 直接嵌入后端，同端口访问
WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")


@app.get("/")
async def root():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok"}
