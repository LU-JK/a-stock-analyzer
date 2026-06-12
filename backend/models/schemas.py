"""Pydantic 响应模型"""
from typing import Optional, Any
from pydantic import BaseModel


# ── 搜索 ──
class StockSearchItem(BaseModel):
    code: str
    name: str
    price: Optional[float] = None
    change_pct: Optional[float] = None
    market_cap: Optional[float] = None

class StockSearchResponse(BaseModel):
    keyword: str
    count: int
    results: list[StockSearchItem]


# ── 实时行情 ──
class RealtimeQuote(BaseModel):
    code: str
    name: str
    price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[int] = None
    turnover: Optional[float] = None
    amplitude: Optional[float] = None
    turnover_rate: Optional[float] = None
    volume_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    float_market_cap: Optional[float] = None
    pe_dynamic: Optional[float] = None
    pb: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None


# ── K线 ──
class KlinePoint(BaseModel):
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: int
    amount: Optional[float] = None

class KlineResponse(BaseModel):
    code: str
    count: int
    data: list[KlinePoint]


# ── 技术指标 ──
class TechnicalSignals(BaseModel):
    ma: str = ""
    macd: str = ""
    rsi: str = ""
    kdj: str = ""

class TechnicalValues(BaseModel):
    MA5: Optional[float] = None
    MA10: Optional[float] = None
    MA20: Optional[float] = None
    MA60: Optional[float] = None
    DIF: Optional[float] = None
    DEA: Optional[float] = None
    MACD_hist: Optional[float] = None
    RSI6: Optional[float] = None
    K: Optional[float] = None
    D: Optional[float] = None
    J: Optional[float] = None

class TechnicalResponse(BaseModel):
    code: str
    signals: TechnicalSignals
    latest_values: TechnicalValues
    kline_data: list[KlinePoint]


# ── 估值 ──
class ValuationResponse(BaseModel):
    code: str
    data: dict[str, Any]


# ── 财务 ──
class FinancialItem(BaseModel):
    date: str
    eps: Optional[float] = None
    revenue_growth: Optional[float] = None
    profit_growth: Optional[float] = None
    roe: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None

class FinancialResponse(BaseModel):
    code: str
    latest: Optional[FinancialItem] = None
    history: list[FinancialItem] = []


# ── 资金流向 ──
class FundFlowItem(BaseModel):
    date: str
    main_net_inflow: Optional[float] = None   # 主力净流入(元)
    super_large_net: Optional[float] = None
    large_net: Optional[float] = None
    medium_net: Optional[float] = None
    small_net: Optional[float] = None

class FundFlowResponse(BaseModel):
    code: str
    data: list[FundFlowItem]


# ── 投资分析 ──
class DimensionScore(BaseModel):
    score: int
    signals: list[str] = []

class AnalysisResponse(BaseModel):
    code: str
    name: str
    total_score: int
    recommendation: str
    dimensions: dict[str, DimensionScore]  # valuation/growth/fund_flow/technical
    spot: Optional[RealtimeQuote] = None
    report_md: str = ""


# ── 市场概览 ──
class IndexItem(BaseModel):
    code: str
    name: str
    price: Optional[float] = None
    change_pct: Optional[float] = None
    change: Optional[float] = None

class SectorItem(BaseModel):
    name: str
    code: str
    change_pct: Optional[float] = None
    main_flow_yuan: Optional[float] = None

class GainerItem(BaseModel):
    code: str
    name: str
    price: Optional[float] = None
    change_pct: Optional[float] = None

class MarketSignals(BaseModel):
    breadth: float = 0
    risk_level: str = "normal"
    top_sector: str = ""

class MarketOverviewResponse(BaseModel):
    meta: dict[str, Any]
    indices: list[IndexItem]
    top_sectors: list[SectorItem]
    top_gainers: list[GainerItem]
    signals: MarketSignals
    errors: list[str] = []
