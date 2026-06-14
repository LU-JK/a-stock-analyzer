"""个股数据 — 新浪API主力 + akshare备用 + 所有失败优雅降级"""
import warnings, sys, os, io, re, urllib.request, asyncio, json
from datetime import datetime, timedelta
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills'))

import akshare as ak
import pandas as pd
import numpy as np
from calc_technical import calc_all_indicators, analyze_signals

_executor = ThreadPoolExecutor(max_workers=8)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.sina.com.cn/",
}


def _run_blocking(fn):
    return asyncio.get_event_loop().run_in_executor(_executor, fn)


def _sf(v):
    try:
        x = float(v)
        return x if np.isfinite(x) else None
    except:
        return None


# ═══════════════════════════════════════════
# 1. 实时行情 (新浪主力)
# ═══════════════════════════════════════════
async def get_realtime_quote(code: str) -> dict:
    prefix = f"sh{code}" if code.startswith('6') else f"sz{code}"

    # 新浪行情（快且稳）
    try:
        url = f"http://hq.sinajs.cn/list={prefix}"
        req = urllib.request.Request(url, headers=HEADERS)
        text = await _run_blocking(lambda: urllib.request.urlopen(req, timeout=8).read().decode('gbk'))
        m = re.search(r'"(.*)"', text)
        if m:
            flds = m.group(1).split(',')
            if len(flds) >= 33 and flds[0]:
                name = flds[0]
                open_, prev = _sf(flds[1]), _sf(flds[2])
                price = _sf(flds[3])
                high, low = _sf(flds[4]), _sf(flds[5])
                vol = int(float(flds[8]) if flds[8] else 0)
                amt = _sf(flds[9])
                change = round(price - prev, 2) if price and prev else None
                pct = round((price - prev) / prev * 100, 2) if price and prev and prev else None
                amplitude = round((high - low) / prev * 100, 2) if high and low and prev else None
                return {
                    "code": code, "name": name, "price": price, "open": open_,
                    "high": high, "low": low, "prev_close": prev,
                    "change": change, "change_pct": pct,
                    "volume": vol, "turnover": amt, "amplitude": amplitude,
                    "turnover_rate": None, "volume_ratio": None,
                    "market_cap": None, "float_market_cap": None,
                    "pe_dynamic": None, "pb": None, "high_52w": None, "low_52w": None,
                }
    except Exception:
        pass

    # 备用：akshare（可能被限流）
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'].astype(str) == code]
        if not row.empty:
            s = row.iloc[0]
            mapping = {
                'code': '代码', 'name': '名称', 'price': '最新价', 'open': '今开',
                'high': '最高', 'low': '最低', 'prev_close': '昨收',
                'change': '涨跌额', 'change_pct': '涨跌幅', 'volume': '成交量',
                'turnover': '成交额', 'amplitude': '振幅', 'turnover_rate': '换手率',
                'volume_ratio': '量比', 'market_cap': '总市值', 'float_market_cap': '流通市值',
                'pe_dynamic': '市盈率-动态', 'pb': '市净率',
            }
            result = {"code": code}
            for en, cn in mapping.items():
                val = s.get(cn)
                if en in ('volume',):
                    result[en] = int(val) if pd.notna(val) else None
                elif en in ('code', 'name'):
                    result[en] = str(val) if pd.notna(val) else ''
                else:
                    result[en] = _sf(val)
            return result
    except Exception as e:
        raise RuntimeError(f"获取行情失败(所有数据源): {e}")


# ═══════════════════════════════════════════
# 2. 历史 K 线
# ═══════════════════════════════════════════
async def get_kline(code: str, days: int = 60) -> dict:
    end = datetime.now().strftime('%Y%m%d')
    start = (datetime.now() - timedelta(days=days + 30)).strftime('%Y%m%d')
    prefix = f"sh{code}" if code.startswith('6') else f"sz{code}"

    try:
        df = await _run_blocking(lambda: ak.stock_zh_a_daily(
            symbol=prefix, start_date=start, end_date=end, adjust="qfq"
        ))
    except Exception:
        raise RuntimeError("获取K线失败: 接口暂时不可用")

    if df is None or df.empty:
        return {"code": code, "count": 0, "data": []}

    df = df.tail(days)
    data = [{"date": str(r.get('date', '')), "open": _sf(r.get('open')),
             "close": _sf(r.get('close')), "high": _sf(r.get('high')),
             "low": _sf(r.get('low')), "volume": int(r.get('volume', 0) or 0),
             "amount": _sf(r.get('amount'))} for _, r in df.iterrows()]
    return {"code": code, "count": len(data), "data": data}


# ═══════════════════════════════════════════
# 3. 技术指标
# ═══════════════════════════════════════════
async def get_technical(code: str, days: int = 120) -> dict:
    end = datetime.now().strftime('%Y%m%d')
    start = (datetime.now() - timedelta(days=days + 60)).strftime('%Y%m%d')
    prefix = f"sh{code}" if code.startswith('6') else f"sz{code}"

    df = await _run_blocking(lambda: ak.stock_zh_a_daily(
        symbol=prefix, start_date=start, end_date=end, adjust="qfq"
    ))
    if df is None or df.empty:
        raise RuntimeError("无K线数据")

    # 列名映射
    col_map = {'open': '开盘', 'close': '收盘', 'high': '最高', 'low': '最低',
               'volume': '成交量', 'amount': '成交额'}
    df_cn = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    df_tech = calc_all_indicators(df_cn)

    signals = analyze_signals(df_tech) or {}
    latest = df_tech.iloc[-1]
    values = {
        "MA5": _sf(latest.get('MA5')), "MA10": _sf(latest.get('MA10')),
        "MA20": _sf(latest.get('MA20')), "MA60": _sf(latest.get('MA60')),
        "DIF": _sf(latest.get('MACD')), "DEA": _sf(latest.get('MACD_signal')),
        "MACD_hist": _sf(latest.get('MACD_hist')), "RSI6": _sf(latest.get('RSI6')),
        "K": _sf(latest.get('K')), "D": _sf(latest.get('D')), "J": _sf(latest.get('J')),
    }

    kline_data = [{
        "date": str(r.get('date', '')), "open": _sf(r.get('open')),
        "close": _sf(r.get('close')), "high": _sf(r.get('high')),
        "low": _sf(r.get('low')), "volume": int(r.get('volume', 0) or 0),
        "amount": _sf(r.get('amount'))
    } for _, r in df.tail(60).iterrows()]

    return {"code": code, "signals": signals, "latest_values": values, "kline_data": kline_data}


# ═══════════════════════════════════════════
# 4. 估值 (优雅降级)
# ═══════════════════════════════════════════
async def get_valuation(code: str) -> dict:
    try:
        prefix = f"SH{code}" if code.startswith('6') else f"SZ{code}"
        xq = await _run_blocking(lambda: ak.stock_individual_spot_xq(symbol=prefix))
        if xq is not None and not xq.empty and 'item' in xq.columns:
            data = {}
            for _, row in xq.iterrows():
                data[str(row['item'])] = str(row.get('value', ''))
            if data:
                return {"code": code, "data": data}
    except Exception:
        pass
    return {"code": code, "data": {}}


# ═══════════════════════════════════════════
# 5. 财务 (akshare, 已验证可用)
# ═══════════════════════════════════════════
async def get_financial(code: str) -> dict:
    try:
        df = await _run_blocking(lambda: ak.stock_financial_analysis_indicator(symbol=code, start_year='2024'))
        history = []
        if df is not None and not df.empty:
            for _, row in df.tail(6).iterrows():
                history.append({
                    "date": str(row.get('日期', '')),
                    "eps": _sf(row.get('摊薄每股收益(元)')),
                    "revenue_growth": _sf(row.get('主营业务收入增长率(%)')),
                    "profit_growth": _sf(row.get('净利润增长率(%)')),
                    "roe": _sf(row.get('净资产收益率(%)')),
                    "gross_margin": _sf(row.get('销售毛利率(%)')),
                    "net_margin": _sf(row.get('销售净利率(%)')),
                })
        return {"code": code, "latest": history[-1] if history else None, "history": history}
    except Exception as e:
        return {"code": code, "latest": None, "history": [], "_error": str(e)}


# ═══════════════════════════════════════════
# 6. 资金流向 (优雅降级)
# ═══════════════════════════════════════════
async def get_fund_flow(code: str, days: int = 10) -> dict:
    try:
        market = 'sh' if code.startswith('6') else 'sz'
        df = await _run_blocking(lambda: ak.stock_individual_fund_flow(stock=code, market=market))
        data = []
        if df is not None and not df.empty:
            for _, row in df.tail(days).iterrows():
                data.append({
                    "date": str(row.get('日期', '')),
                    "main_net_inflow": _sf(row.get('主力净流入-净额')),
                    "super_large_net": _sf(row.get('超大单净流入-净额')),
                    "large_net": _sf(row.get('大单净流入-净额')),
                    "medium_net": _sf(row.get('中单净流入-净额')),
                    "small_net": _sf(row.get('小单净流入-净额')),
                })
        return {"code": code, "data": data}
    except Exception:
        return {"code": code, "data": [], "_unavailable": True}


# ═══════════════════════════════════════════
# 7. 综合投资分析 (部分数据不可用时仍给分)
# ═══════════════════════════════════════════
async def get_investment_analysis(code: str) -> dict:
    # 并行获取可用数据（失败不阻塞）
    results = {}
    coros = {
        'spot': get_realtime_quote(code),
        'tech': get_technical(code, days=120),
        'fin': get_financial(code),
        'fund': get_fund_flow(code, days=10),
    }
    for k, coro in coros.items():
        try:
            results[k] = await coro
        except Exception as e:
            results[k] = None

    spot = results.get('spot') or {}
    tech = results.get('tech') or {}
    fin = results.get('fin') or {}
    fund = results.get('fund') or {}

    dims = {}
    has_fund = fund.get('data') and not fund.get('_unavailable')

    # 1. 估值 (从行情PE/PB推断)
    pe, pb = spot.get('pe_dynamic'), spot.get('pb')
    if pe is not None:
        if pe < 0:
            dims['valuation'] = {'score': 20, 'signals': ['PE为负，公司亏损']}
        elif pe < 15:
            dims['valuation'] = {'score': 80, 'signals': [f'PE={pe:.1f}，估值偏低']}
        elif pe < 35:
            dims['valuation'] = {'score': 55, 'signals': [f'PE={pe:.1f}，估值适中']}
        else:
            dims['valuation'] = {'score': 30, 'signals': [f'PE={pe:.1f}，估值偏高']}
    else:
        dims['valuation'] = {'score': 50, 'signals': ['PE数据缺失']}

    # 2. 成长性
    latest_fin = fin.get('latest')
    if latest_fin and latest_fin.get('revenue_growth') is not None:
        rg = latest_fin.get('revenue_growth', 0) or 0
        pg = latest_fin.get('profit_growth', 0) or 0
        sigs = []
        if rg > 20:
            sigs.append(f'营收增速{rg:.1f}%，快速增长')
            gs = 80
        elif rg > 0:
            sigs.append(f'营收增速{rg:.1f}%，缓慢增长')
            gs = 60
        else:
            sigs.append(f'营收增速{rg:.1f}%，下滑')
            gs = 35
        if pg > 20:
            sigs.append(f'利润增速{pg:.1f}%，优秀')
            gs = min(gs + 10, 100)
        elif pg > 0:
            sigs.append(f'利润增速{pg:.1f}%，一般')
        else:
            sigs.append(f'利润增速{pg:.1f}%，下滑')
            gs = max(gs - 10, 10)
        dims['growth'] = {'score': gs, 'signals': sigs}
    else:
        dims['growth'] = {'score': 50, 'signals': ['财务数据暂时不可用']}

    # 3. 资金面
    if has_fund:
        fd = fund['data']
        total = sum(x.get('main_net_inflow') or 0 for x in fd)
        if total > 1e8:
            dims['fund_flow'] = {'score': 78, 'signals': [f'近10日主力净流入{total/1e8:.1f}亿']}
        elif total > 0:
            dims['fund_flow'] = {'score': 60, 'signals': ['主力小幅净流入']}
        elif total > -5e7:
            dims['fund_flow'] = {'score': 45, 'signals': ['主力小幅净流出']}
        else:
            dims['fund_flow'] = {'score': 25, 'signals': [f'主力净流出{abs(total)/1e8:.1f}亿']}
    else:
        dims['fund_flow'] = {'score': 50, 'signals': ['资金数据不可用']}

    # 4. 技术面
    tech_sigs = tech.get('signals', {}) if tech else {}
    bullish = sum(1 for v in str(tech_sigs.values()) if '多头' in v or '偏强' in v)
    bearish = sum(1 for v in str(tech_sigs.values()) if '空头' in v or '偏弱' in v)
    ts = 50 + (bullish - bearish) * 15
    ts = max(10, min(100, ts))
    dims['technical'] = {'score': ts, 'signals': [f'{k}:{v}' for k, v in tech_sigs.items()]}

    # 总分
    w = {'valuation': 0.3, 'growth': 0.3, 'fund_flow': 0.2, 'technical': 0.2}
    total = sum(dims[k]['score'] * w[k] for k in dims)
    total = round(total)

    rec = "🟢 积极 — 综合表现良好" if total >= 70 else ("🟡 观望 — 表现一般" if total >= 40 else "🔴 谨慎 — 风险较高")

    # 生成简单报告
    dim_names = {'valuation': '估值', 'growth': '成长', 'fund_flow': '资金', 'technical': '技术'}
    lines = [f"# {code} {spot.get('name', '')} 投资分析", f"**综合评分: {total}/100**", f"**{rec}**", ""]
    for k, v in dims.items():
        lines.append(f"## {dim_names.get(k, k)} (得分: {v['score']})")
        for s in v.get('signals', []):
            lines.append(f"- {s}")
        lines.append("")

    return {
        "code": code, "name": spot.get('name', code),
        "total_score": total, "recommendation": rec,
        "dimensions": dims, "spot": spot,
        "report_md": '\n'.join(lines),
    }
