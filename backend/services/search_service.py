"""股票搜索服务 — 按名称或代码搜索 A 股"""
import warnings
warnings.filterwarnings('ignore')

import akshare as ak
import pandas as pd


def search_stocks(keyword: str, limit: int = 20) -> list[dict]:
    """
    搜索股票：在全部 A 股中按名称(含拼音)或代码匹配
    返回: [{"code": "600519", "name": "贵州茅台", "price": ..., "change_pct": ..., "market_cap": ...}, ...]
    """
    if not keyword or len(keyword.strip()) < 1:
        return []

    keyword = keyword.strip()

    try:
        # 获取全部 A 股实时行情 (包含名称和代码)
        df = ak.stock_zh_a_spot_em()

        # 强制代码为字符串
        df['代码'] = df['代码'].astype(str)

        # 筛选: 代码以 keyword 开头 或 名称包含 keyword
        mask_code = df['代码'].str.startswith(keyword)
        mask_name = df['名称'].str.contains(keyword, case=False, na=False)

        result = df[mask_code | mask_name].copy()

        if result.empty:
            return []

        # 按成交额降序，取前 limit
        if '成交额' in result.columns:
            result['成交额_num'] = pd.to_numeric(result['成交额'], errors='coerce').fillna(0)
            result = result.sort_values('成交额_num', ascending=False)
        elif '量比' in result.columns:
            result = result.sort_values('量比', ascending=False)

        result = result.head(limit)

        items = []
        for _, row in result.iterrows():
            try:
                price = float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None
                change_pct = float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None
                mcap = float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None
            except (ValueError, TypeError):
                price, change_pct, mcap = None, None, None

            items.append({
                "code": row['代码'],
                "name": row['名称'],
                "price": price,
                "change_pct": change_pct,
                "market_cap": mcap,
            })

        return items

    except Exception as e:
        raise RuntimeError(f"搜索股票失败: {e}")
