"""个股数据服务 — 实时行情/K线/技术/估值/财务/资金/投资分析"""
import warnings
warnings.filterwarnings('ignore')

import sys
import os
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import akshare as ak
import pandas as pd
import numpy as np

# 技术指标模块 — 已包含在项目中
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")
sys.path.insert(0, SKILLS_DIR)
from calc_technical import calc_all_indicators, analyze_signals

# 线程池，用于执行 ak 阻塞调用
_executor = ThreadPoolExecutor(max_workers=8)


def _run_blocking(func, *args, **kwargs):
    """在线程池中运行阻塞函数"""
    fn = partial(func, *args, **kwargs)
    return asyncio.get_event_loop().run_in_executor(_executor, fn)


# ── 行情字段映射 ──
_QUOTE_FIELDS = {
    '最新价': 'price', '今开': 'open', '最高': 'high', '最低': 'low',
    '昨收': 'prev_close', '成交量': 'volume', '成交额': 'turnover',
    '涨跌幅': 'change_pct', '涨跌额': 'change', '振幅': 'amplitude',
    '换手率': 'turnover_rate', '量比': 'volume_ratio',
    '总市值': 'market_cap', '流通市值': 'float_market_cap',
    '市盈率-动态': 'pe_dynamic', '市净率': 'pb',
    '60日涨跌幅': 'pct_60d', '52周最高': 'high_52w', '52周最低': 'low_52w',
    '名称': 'name', '代码': 'code',
}


def _safe_float(val) -> Optional[float]:
    try:
        v = float(val)
        return v if np.isfinite(v) else None
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════
# 1. 实时行情
# ═══════════════════════════════════════════
async def get_realtime_quote(code: str) -> dict:
    """获取单只股票实时行情"""
    try:
        df = await _run_blocking(ak.stock_zh_a_spot_em)
        row = df[df['代码'].astype(str) == code]
        if row.empty:
            raise ValueError(f"未找到股票代码 {code}")

        s = row.iloc[0]
        result = {"code": str(code)}
        for cn, en in _QUOTE_FIELDS.items():
            if cn in s.index:
                val = s[cn]
                if en in ('volume',):
                    result[en] = int(val) if pd.notna(val) else None
                elif en in ('code', 'name'):
                    result[en] = str(val)
                else:
                    result[en] = _safe_float(val)

        return result
    except Exception as e:
        raise RuntimeError(f"获取行情失败: {e}")


# ═══════════════════════════════════════════
# 2. 历史 K 线
# ═══════════════════════════════════════════
async def get_kline(code: str, days: int = 60, period: str = "daily") -> dict:
    """获取历史 K 线"""
    try:
        end = datetime.now().strftime('%Y%m%d')
        start = (datetime.now() - timedelta(days=days + 30)).strftime('%Y%m%d')

        df = await _run_blocking(
            ak.stock_zh_a_daily,
            symbol=f"sh{code}" if code.startswith('6') else f"sz{code}",
            start_date=start, end_date=end, adjust="qfq"
        )

        if df.empty:
            return {"code": code, "count": 0, "data": []}

        # 取最近 days 条
        df = df.tail(days)

        data = []
        for _, row in df.iterrows():
            data.append({
                "date": str(row.get('date', '')),
                "open": _safe_float(row.get('open')),
                "close": _safe_float(row.get('close')),
                "high": _safe_float(row.get('high')),
                "low": _safe_float(row.get('low')),
                "volume": int(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0,
                "amount": _safe_float(row.get('amount')),
            })

        return {"code": code, "count": len(data), "data": data}
    except Exception as e:
        raise RuntimeError(f"获取K线失败: {e}")


# ═══════════════════════════════════════════
# 3. 技术指标
# ═══════════════════════════════════════════
async def get_technical(code: str, days: int = 120) -> dict:
    """计算技术指标"""
    try:
        end = datetime.now().strftime('%Y%m%d')
        start = (datetime.now() - timedelta(days=days + 60)).strftime('%Y%m%d')

        df = await _run_blocking(
            ak.stock_zh_a_daily,
            symbol=f"sh{code}" if code.startswith('6') else f"sz{code}",
            start_date=start, end_date=end, adjust="qfq"
        )

        if df.empty:
            raise ValueError(f"未找到K线数据")

        # stock_zh_a_daily 返回英文列名, calc_technical 需要中文列名
        col_map = {'open': '开盘', 'close': '收盘', 'high': '最高',
                   'low': '最低', 'volume': '成交量', 'amount': '成交额'}
        df_cn = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        # 计算技术指标
        df_tech = calc_all_indicators(df_cn)
        # 恢复英文列名以便后续使用
        df = df_cn.rename(columns={v: k for k, v in col_map.items()})
        signals = analyze_signals(df_tech)

        latest = df_tech.iloc[-1]
        values = {
            "MA5": _safe_float(latest.get('MA5')),
            "MA10": _safe_float(latest.get('MA10')),
            "MA20": _safe_float(latest.get('MA20')),
            "MA60": _safe_float(latest.get('MA60')),
            "DIF": _safe_float(latest.get('MACD')),
            "DEA": _safe_float(latest.get('MACD_signal')),
            "MACD_hist": _safe_float(latest.get('MACD_hist')),
            "RSI6": _safe_float(latest.get('RSI6')),
            "K": _safe_float(latest.get('K')),
            "D": _safe_float(latest.get('D')),
            "J": _safe_float(latest.get('J')),
        }

        # K 线数据（最近60条，给前端画图）
        kline_data = []
        for _, row in df.tail(60).iterrows():
            kline_data.append({
                "date": str(row.get('date', '')),
                "open": _safe_float(row.get('open')),
                "close": _safe_float(row.get('close')),
                "high": _safe_float(row.get('high')),
                "low": _safe_float(row.get('low')),
                "volume": int(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0,
                "amount": _safe_float(row.get('amount')),
            })

        return {
            "code": code,
            "signals": signals,  # calc_technical 的 analyze_signals 返回 dict
            "latest_values": values,
            "kline_data": kline_data,
        }
    except Exception as e:
        raise RuntimeError(f"计算技术指标失败: {e}")


# ═══════════════════════════════════════════
# 4. 估值数据
# ═══════════════════════════════════════════
async def get_valuation(code: str) -> dict:
    """获取估值指标"""
    try:
        prefix = f"SH{code}" if code.startswith('6') else f"SZ{code}"
        xq = await _run_blocking(ak.stock_individual_spot_xq, symbol=prefix)

        data = {}
        if xq is not None and not xq.empty:
            for _, row in xq.iterrows():
                data[str(row['item'])] = str(row['value'])

        return {"code": code, "data": data}
    except Exception as e:
        raise RuntimeError(f"获取估值失败: {e}")


# ═══════════════════════════════════════════
# 5. 财务数据
# ═══════════════════════════════════════════
async def get_financial(code: str) -> dict:
    try:
        df = await _run_blocking(ak.stock_financial_analysis_indicator, symbol=code, start_year='2024')

        history = []
        if df is not None and not df.empty:
            for _, row in df.tail(6).iterrows():
                history.append({
                    "date": str(row.get('日期', '')),
                    "eps": _safe_float(row.get('摊薄每股收益(元)')),
                    "revenue_growth": _safe_float(row.get('主营业务收入增长率(%)')),
                    "profit_growth": _safe_float(row.get('净利润增长率(%)')),
                    "roe": _safe_float(row.get('净资产收益率(%)')),
                    "gross_margin": _safe_float(row.get('销售毛利率(%)')),
                    "net_margin": _safe_float(row.get('销售净利率(%)')),
                })

        latest = history[-1] if history else None
        return {"code": code, "latest": latest, "history": history}
    except Exception as e:
        raise RuntimeError(f"获取财务数据失败: {e}")


# ═══════════════════════════════════════════
# 6. 资金流向
# ═══════════════════════════════════════════
async def get_fund_flow(code: str, days: int = 10) -> dict:
    try:
        market = 'sh' if code.startswith('6') else 'sz'
        df = await _run_blocking(ak.stock_individual_fund_flow, stock=code, market=market)

        data = []
        if df is not None and not df.empty:
            for _, row in df.tail(days).iterrows():
                data.append({
                    "date": str(row.get('日期', '')),
                    "main_net_inflow": _safe_float(row.get('主力净流入-净额')),
                    "super_large_net": _safe_float(row.get('超大单净流入-净额')),
                    "large_net": _safe_float(row.get('大单净流入-净额')),
                    "medium_net": _safe_float(row.get('中单净流入-净额')),
                    "small_net": _safe_float(row.get('小单净流入-净额')),
                })

        return {"code": code, "data": data}
    except Exception as e:
        raise RuntimeError(f"获取资金流向失败: {e}")


# ═══════════════════════════════════════════
# 7. 综合投资分析
# ═══════════════════════════════════════════
async def get_investment_analysis(code: str) -> dict:
    """综合投资分析 — 多维度评分"""
    try:
        # 并行获取多个数据源
        spot_future = get_realtime_quote(code)
        kline_future = get_kline(code, days=60)
        # 财务和资金也并行
        financial_future = get_financial(code)
        fund_future = get_fund_flow(code, days=10)

        spot, kline, financial, fund_flow = await asyncio.gather(
            spot_future, kline_future, financial_future, fund_future
        )

        # ── 计算各项评分 ──
        scores = {}
        signals_map = {}

        # 1. 估值评分
        pe = spot.get('pe_dynamic')
        pb = spot.get('pb')
        val_signals = []
        if pe is not None:
            if pe < 0:
                val_signals.append("PE为负，公司亏损")
                val_score = 20
            elif pe < 15:
                val_signals.append("PE<15，估值偏低")
                val_score = 80
            elif pe < 30:
                val_signals.append("PE在15-30之间，估值适中")
                val_score = 60
            elif pe < 60:
                val_signals.append("PE在30-60之间，估值偏高")
                val_score = 40
            else:
                val_signals.append("PE>60，估值过高")
                val_score = 20
        else:
            val_score = 50
        if pb is not None:
            if pb < 1:
                val_signals.append("PB<1，破净")
                val_score = min(val_score + 10, 100)
            elif pb < 5:
                val_signals.append("PB合理")
            else:
                val_signals.append("PB偏高")
                val_score = max(val_score - 10, 10)
        scores['valuation'] = {'score': val_score, 'signals': val_signals}

        # 2. 成长性评分
        growth_signals = []
        latest = financial.get('latest')
        if latest:
            rev_g = latest.get('revenue_growth') or 0
            prof_g = latest.get('profit_growth') or 0
            if rev_g > 20:
                growth_signals.append(f"营收增速{rev_g:.1f}%，快速增长")
                growth_score = 80
            elif rev_g > 0:
                growth_signals.append(f"营收增速{rev_g:.1f}%，缓慢增长")
                growth_score = 60
            else:
                growth_signals.append(f"营收增速{rev_g:.1f}%，下滑")
                growth_score = 30

            if prof_g > 20:
                growth_signals.append(f"利润增速{prof_g:.1f}%，优秀")
                growth_score = min(growth_score + 10, 100)
            elif prof_g > 0:
                growth_signals.append(f"利润增速{prof_g:.1f}%，一般")
            else:
                growth_signals.append(f"利润增速{prof_g:.1f}%，下滑")
                growth_score = max(growth_score - 15, 10)
        else:
            growth_score = 50
        scores['growth'] = {'score': growth_score, 'signals': growth_signals}

        # 3. 资金面评分
        fund_signals = []
        fund_data = fund_flow.get('data', [])
        if fund_data:
            total_inflow = sum(
                (item.get('main_net_inflow') or 0) for item in fund_data
            )
            if total_inflow > 1e8:
                fund_signals.append(f"近{days}日主力净流入{total_inflow/1e8:.1f}亿，积极")
                fund_score = 80
            elif total_inflow > 0:
                fund_signals.append(f"主力小幅净流入{total_inflow/1e4:.0f}万")
                fund_score = 60
            elif total_inflow > -1e8:
                fund_signals.append(f"主力小幅净流出")
                fund_score = 45
            else:
                fund_signals.append(f"近{days}日主力净流出{abs(total_inflow)/1e8:.1f}亿，偏空")
                fund_score = 25
        else:
            fund_score = 50
        scores['fund_flow'] = {'score': fund_score, 'signals': fund_signals}

        # 4. 技术面评分
        # 先快速获取技术指标
        tech = await get_technical(code, days=120)
        tech_signals_dict = tech.get('signals', {})
        tech_signals = [f"{k}: {v}" for k, v in tech_signals_dict.items()]
        # 简单评分: 多头信号多则高分
        bullish = sum(
            1 for v in tech_signals_dict.values()
            if '多头' in str(v) or '偏强' in str(v) or '金叉' in str(v)
        )
        bearish = sum(
            1 for v in tech_signals_dict.values()
            if '空头' in str(v) or '偏弱' in str(v) or '死叉' in str(v)
        )
        tech_score = 50 + (bullish - bearish) * 15
        tech_score = max(10, min(100, tech_score))
        scores['technical'] = {'score': tech_score, 'signals': tech_signals}

        # 综合总分
        weights = {'valuation': 0.3, 'growth': 0.3, 'fund_flow': 0.2, 'technical': 0.2}
        total = sum(scores[k]['score'] * weights[k] for k in weights)

        # 建议
        if total >= 75:
            rec = "🟢 积极 — 综合表现良好，可考虑介入"
        elif total >= 55:
            rec = "🟡 观望 — 表现一般，建议等待或小仓位"
        else:
            rec = "🔴 谨慎 — 风险较高，建议观望"

        name = spot.get('name', code)

        return {
            "code": code,
            "name": name,
            "total_score": round(total),
            "recommendation": rec,
            "dimensions": scores,
            "spot": spot,
            "report_md": "",
        }

    except Exception as e:
        raise RuntimeError(f"投资分析失败: {e}")
