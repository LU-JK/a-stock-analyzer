"""市场数据 — a-stock-data 主力 + 备用"""
import sys, os, asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills'))
from a_stock_data import fetch_snapshot


async def get_market_overview() -> dict:
    """市场全景快照，失败时返回空数据而非报错"""
    try:
        data = await asyncio.get_event_loop().run_in_executor(None, fetch_snapshot)
        return {
            "meta": data.get("meta", {}),
            "indices": data.get("indices", []),
            "top_sectors": data.get("sectors", [])[:10],
            "top_gainers": data.get("gainers", [])[:10],
            "signals": data.get("signals", {}),
            "errors": data.get("errors", []),
        }
    except Exception:
        # 降级：返回空数据
        return {
            "meta": {"market_open": False, "timestamp": ""},
            "indices": [],
            "top_sectors": [],
            "top_gainers": [],
            "signals": {"breadth": 0, "risk_level": "unknown", "top_sector": ""},
            "errors": ["市场数据接口暂时不可用"],
        }
