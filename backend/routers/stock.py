"""个股路由 — /api/v1/stocks/*"""
from fastapi import APIRouter, Query, HTTPException

from services import search_service, stock_service

router = APIRouter()


@router.get("/stocks/search")
async def search_stocks(
    keyword: str = Query(..., description="搜索关键词（名称或代码）"),
    limit: int = Query(20, ge=1, le=50, description="返回数量上限")
):
    """搜索股票"""
    try:
        results = search_service.search_stocks(keyword, limit)
        return {"keyword": keyword, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{code}/realtime")
async def realtime_quote(code: str):
    """实时行情"""
    try:
        return await stock_service.get_realtime_quote(code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{code}/kline")
async def history_kline(
    code: str,
    days: int = Query(60, ge=5, le=365, description="K线数量"),
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$")
):
    """历史K线"""
    try:
        return await stock_service.get_kline(code, days, period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{code}/technical")
async def technical_indicators(
    code: str,
    days: int = Query(120, ge=30, le=365, description="计算天数")
):
    """技术指标"""
    try:
        return await stock_service.get_technical(code, days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{code}/valuation")
async def valuation(code: str):
    """估值数据"""
    try:
        return await stock_service.get_valuation(code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{code}/financial")
async def financial(code: str):
    """财务数据"""
    try:
        return await stock_service.get_financial(code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{code}/fund-flow")
async def fund_flow(
    code: str,
    days: int = Query(10, ge=1, le=60, description="查询天数")
):
    """资金流向"""
    try:
        return await stock_service.get_fund_flow(code, days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{code}/analysis")
async def investment_analysis(code: str):
    """综合投资分析"""
    try:
        return await stock_service.get_investment_analysis(code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
