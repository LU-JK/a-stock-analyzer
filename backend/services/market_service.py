"""市场数据服务 — 指数、板块、涨幅榜"""
import warnings
warnings.filterwarnings('ignore')

import sys
import os
import asyncio

# 市场数据模块 — 已包含在项目中
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")
sys.path.insert(0, SKILLS_DIR)
from a_stock_data import fetch_snapshot


async def get_market_overview() -> dict:
    """获取市场全景快照"""
    try:
        # fetch_snapshot 是纯 HTTP 请求，同步但很快
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, fetch_snapshot)

        return {
            "meta": data.get("meta", {}),
            "indices": data.get("indices", []),
            "top_sectors": data.get("sectors", [])[:10],
            "top_gainers": data.get("gainers", [])[:10],
            "signals": data.get("signals", {}),
            "errors": data.get("errors", []),
        }
    except Exception as e:
        raise RuntimeError(f"获取市场数据失败: {e}")
