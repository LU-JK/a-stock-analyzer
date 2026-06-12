#!/usr/bin/env python
import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, time
from zoneinfo import ZoneInfo

CN_TZ = ZoneInfo("Asia/Shanghai")
VERSION = "1.0.0"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://quote.eastmoney.com/",
}


def fetch_snapshot() -> dict:
    errors = []
    now = datetime.now(CN_TZ)
    indices = _safe("indices", fetch_indices, errors)
    sectors = _safe("sectors", fetch_sectors, errors)
    gainers = _safe("gainers", fetch_gainers, errors)
    active = _safe("active", fetch_active, errors)
    return {
        "meta": {
            "version": VERSION,
            "provider": "eastmoney-public",
            "timestamp": now.isoformat(timespec="seconds"),
            "market_open": is_market_open(now),
        },
        "indices": indices,
        "sectors": sectors,
        "gainers": gainers,
        "active": active,
        "signals": build_signals(indices, sectors, gainers),
        "candidate_pool": rank_candidates(indices, sectors, gainers, active),
        "errors": errors,
    }


def fetch_indices() -> list[dict]:
    url = (
        "https://push2.eastmoney.com/api/qt/ulist.np/get"
        "?fltt=2&fields=f12,f14,f2,f3,f4&secids=1.000001,0.399001,0.399006,1.000688"
    )
    data = _fetch_json(url)
    rows = []
    for item in data.get("data", {}).get("diff", []):
        rows.append(
            {
                "code": str(item.get("f12", "")),
                "name": item.get("f14", ""),
                "price": _num(item.get("f2")),
                "change_pct": _num(item.get("f3")),
                "change": _num(item.get("f4")),
            }
        )
    return rows


def fetch_sectors(limit: int = 80) -> list[dict]:
    url = (
        "https://push2.eastmoney.com/api/qt/clist/get"
        f"?cb=&pn=1&pz={limit}&po=1&np=1"
        "&fields=f12,f14,f3,f62,f184,f20,f104,f8,f15,f16"
        "&fs=m:90+t:2"
    )
    data = _fetch_json(url)
    rows = []
    for item in data.get("data", {}).get("diff", []):
        rows.append(
            {
                "code": item.get("f12", ""),
                "name": item.get("f14", ""),
                "change_pct": _num(item.get("f3")),
                "main_flow_yuan": _num(item.get("f184")),
                "turnover_yuan": _num(item.get("f62")),
                "market_cap_yuan": _num(item.get("f20")),
                "pe_ratio": _num(item.get("f104")),
                "up_count": _num(item.get("f8")),
                "down_count": _num(item.get("f15")),
            }
        )
    rows.sort(key=lambda row: row["change_pct"], reverse=True)
    return rows


def fetch_gainers(limit: int = 30) -> list[dict]:
    url = (
        "https://push2.eastmoney.com/api/qt/clist/get"
        f"?cb=&pn=1&pz={limit}&po=1&np=1"
        "&fields=f12,f14,f2,f3,f4,f5,f6,f15,f16,f17,f62,f184,f8"
        "&fs=m:0+t:6+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2"
        "&fltt=2"
    )
    data = _fetch_json(url)
    rows = []
    for item in data.get("data", {}).get("diff", []):
        change_pct = _num(item.get("f3"))
        if change_pct <= 0:
            continue
        rows.append(
            {
                "code": item.get("f12", ""),
                "name": item.get("f14", ""),
                "price": _num(item.get("f2")),
                "change_pct": change_pct,
                "change": _num(item.get("f4")),
                "volume": _num(item.get("f5")),
                "turnover_yuan": _num(item.get("f6")),
                "main_flow_yuan": _num(item.get("f184")),
            }
        )
    rows.sort(key=lambda row: row["change_pct"], reverse=True)
    return rows


def fetch_active(limit: int = 30) -> list[dict]:
    url = (
        "https://push2.eastmoney.com/api/qt/clist/get"
        f"?cb=&pn=1&pz={limit}&po=1&np=1"
        "&fields=f12,f14,f2,f3,f5,f6,f62,f184"
        "&fs=m:0+t:6+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2"
        "&fid=f6&fltt=2"
    )
    data = _fetch_json(url)
    rows = []
    for item in data.get("data", {}).get("diff", []):
        rows.append(
            {
                "code": item.get("f12", ""),
                "name": item.get("f14", ""),
                "price": _num(item.get("f2")),
                "change_pct": _num(item.get("f3")),
                "volume": _num(item.get("f5")),
                "turnover_yuan": _num(item.get("f6")),
                "main_flow_yuan": _num(item.get("f184")),
            }
        )
    return rows


def build_signals(indices: list[dict], sectors: list[dict], gainers: list[dict]) -> dict:
    positive_sectors = [row for row in sectors if row.get("change_pct", 0) > 0]
    breadth = round(len(positive_sectors) / len(sectors) * 100, 1) if sectors else 0
    risk_level = "normal"
    if breadth < 25:
        risk_level = "cautious"
    elif breadth > 65:
        risk_level = "warm"
    return {
        "breadth": breadth,
        "risk_level": risk_level,
        "top_sector": sectors[0]["name"] if sectors else "",
        "top_gainer": gainers[0]["name"] if gainers else "",
        "index_avg_change": round(sum(row.get("change_pct", 0) for row in indices) / len(indices), 2) if indices else 0,
    }


def rank_candidates(indices: list[dict], sectors: list[dict], gainers: list[dict], active: list[dict], limit: int = 5) -> list[dict]:
    active_by_code = {row.get("code"): row for row in active}
    sector_bonus = 12 if sectors and sectors[0].get("change_pct", 0) > 2 else 6 if sectors else 0
    index_avg = sum(row.get("change_pct", 0) for row in indices) / len(indices) if indices else 0
    market_bonus = max(-8, min(8, index_avg * 2))
    candidates = []
    for row in gainers[:20]:
        code = row.get("code", "")
        active_row = active_by_code.get(code, {})
        trend = min(35, max(0, row.get("change_pct", 0) * 3.2))
        flow = 10 if row.get("main_flow_yuan", 0) > 0 else 0
        liquidity = min(18, max(0, row.get("turnover_yuan", active_row.get("turnover_yuan", 0)) / 100000000))
        risk = 10 if row.get("change_pct", 0) >= 9.5 else 0
        score = round(max(0, min(100, trend + flow + liquidity + sector_bonus + market_bonus - risk)), 1)
        evidence = []
        if row.get("change_pct", 0) > 0:
            evidence.append(f"涨幅 {row.get('change_pct', 0):.2f}%")
        if row.get("turnover_yuan", 0):
            evidence.append("成交额活跃")
        if flow:
            evidence.append("主力资金字段为正")
        if sector_bonus:
            evidence.append("市场板块热度提供加分")
        action = "watch"
        position = 0
        if score >= 70 and risk == 0:
            action = "focus"
            position = 5
        elif score >= 55 and risk == 0:
            action = "watch"
            position = 3
        candidates.append(
            {
                "rank": 0,
                "code": code,
                "name": row.get("name", ""),
                "score": score,
                "action": action,
                "position_pct": position,
                "entry": "放量突破或回踩确认",
                "stop_loss": "-5%",
                "take_profit": "+8% to +12%",
                "evidence": evidence,
                "risk_flags": ["接近涨停不追高"] if risk else [],
                "factors": {
                    "trend": round(trend, 1),
                    "flow": flow,
                    "event": 0,
                    "sector": sector_bonus,
                    "risk": risk,
                },
            }
        )
    candidates = [row for row in candidates if row["evidence"]]
    candidates.sort(key=lambda row: row["score"], reverse=True)
    for idx, row in enumerate(candidates[:limit], 1):
        row["rank"] = idx
    return candidates[:limit]


def is_market_open(dt: datetime | None = None) -> bool:
    dt = dt or datetime.now(CN_TZ)
    if dt.weekday() >= 5:
        return False
    current = dt.time()
    return time(9, 30) <= current <= time(11, 30) or time(13, 0) <= current <= time(15, 0)


def _safe(name: str, fn, errors: list[str]):
    try:
        return fn()
    except Exception as exc:
        errors.append(f"{name}: {exc}")
        return []


def _fetch_json(url: str, timeout: int = 12) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    if raw.startswith("(") or raw.startswith("jQuery"):
        match = re.search(r"\((\{.*\})\)", raw, re.DOTALL)
        if match:
            raw = match.group(1)
    return json.loads(raw)


def _num(value) -> float:
    try:
        if value in (None, "-", ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch public A-share market data.")
    sub = parser.add_subparsers(dest="command")
    snap = sub.add_parser("snapshot", help="Print a normalized market snapshot.")
    snap.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    rank = sub.add_parser("rank", help="Print top AstraTrade-style candidates.")
    rank.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args(argv)
    if args.command in (None, "snapshot"):
        data = fetch_snapshot()
        print(json.dumps(data, ensure_ascii=False, indent=2 if getattr(args, "pretty", False) else None))
        return 0 if not data["errors"] else 2
    if args.command == "rank":
        data = fetch_snapshot()
        print(json.dumps(data["candidate_pool"], ensure_ascii=False, indent=2 if getattr(args, "pretty", False) else None))
        return 0 if data["candidate_pool"] else 2
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
