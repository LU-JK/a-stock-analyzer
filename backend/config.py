"""后端配置"""
import os

# 服务器 — 云平台会通过 PORT 环境变量指定端口
PORT = int(os.getenv("PORT", "8000"))

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")

# API 前缀
API_PREFIX = "/api/v1"
