"""市场路由 — /api/v1/market/*"""
from fastapi import APIRouter, HTTPException

from services import market_service

router = APIRouter()


@router.get("/market/overview")
async def market_overview():
    """市场全景"""
    try:
        return await market_service.get_market_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
