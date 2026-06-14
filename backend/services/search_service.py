"""股票搜索 — akshare 建缓存 + 新浪API补价格"""
import warnings
warnings.filterwarnings('ignore')

import json, os, time, re, urllib.request

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "cache", "stock_map.json")
CACHE_TTL = 86400  # 24小时

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.sina.com.cn/",
}


def _build_cache() -> list[dict]:
    """用 akshare 获取全量股票名称代码映射（仅第一次/缓存过期时调用）"""
    import akshare as ak
    df = ak.stock_info_a_code_name()
    stocks = []
    for _, row in df.iterrows():
        stocks.append({"code": str(row["code"]), "name": str(row["name"])})
    return stocks


def _get_all_stocks() -> list[dict]:
    """获取全量股票列表（缓存优先）"""
    # 读缓存
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if time.time() - data.get("ts", 0) < CACHE_TTL:
                return data.get("stocks", [])
        except:
            pass

    # 构建新缓存
    stocks = _build_cache()
    if stocks:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "stocks": stocks}, f, ensure_ascii=False)
    return stocks


def _fetch_prices_sina(codes: list[str]) -> dict[str, dict]:
    """新浪API批量获取实时价"""
    prefixes = [f"sh{c}" if c.startswith("6") else f"sz{c}" for c in codes]
    url = f"http://hq.sinajs.cn/list={','.join(prefixes)}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        text = urllib.request.urlopen(req, timeout=8).read().decode("gbk")
        results = {}
        for line in text.strip().split("\n"):
            m = re.match(r"var hq_str_(\w+)=\"(.+)\"", line)
            if m:
                short = m.group(1)[2:]
                flds = m.group(2).split(",")
                if len(flds) >= 4 and flds[0]:
                    try:
                        price = float(flds[3]) if flds[3] else 0
                        prev = float(flds[2]) if flds[2] else 0
                        results[short] = {
                            "price": price,
                            "change_pct": round((price-prev)/prev*100,2) if prev else None
                        }
                    except: pass
        return results
    except:
        return {}


def search_stocks(keyword: str, limit: int = 20) -> list[dict]:
    """搜索股票：名称模糊匹配 + 代码前缀匹配"""
    kw = keyword.strip()
    if not kw:
        return []

    stocks = _get_all_stocks()

    # 匹配
    matches = []
    for s in stocks:
        if kw in s["name"] or s["code"].startswith(kw):
            matches.append(s)
        if len(matches) >= limit * 3:
            break

    if not matches:
        return []

    # 取前 N 只，补充价格
    top = matches[:limit]
    codes = [s["code"] for s in top]
    prices = _fetch_prices_sina(codes)

    result = []
    for s in top:
        p = prices.get(s["code"], {})
        result.append({
            "code": s["code"],
            "name": s["name"],
            "price": p.get("price"),
            "change_pct": p.get("change_pct"),
            "market_cap": None,
        })
    return result
