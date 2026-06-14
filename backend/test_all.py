"""一键全量测试"""
import sys,io,os,time,json
sys.path.insert(0,os.path.dirname(__file__))
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')

FAILS=[]

def t(name,fn):
    global FAILS
    print(f'\n=== {name} ===')
    s=time.time()
    try:
        fn()
        print(f'  OK ({time.time()-s:.1f}s)')
    except Exception as e:
        print(f'  FAIL: {e}')
        FAILS.append(name)

import asyncio
from services.search_service import search_stocks
from services.stock_service import get_realtime_quote,get_kline,get_technical,get_valuation,get_financial,get_fund_flow,get_investment_analysis
from services.market_service import get_market_overview

# 1. 搜索
def t1():
    for kw in ['603002','茅台','科技','60']:
        r=search_stocks(kw,3)
        assert len(r)>0,f'搜索"{kw}"无结果'
        print(f'  "{kw}": {r[0]["name"]} ¥{r[0].get("price","?")}')

# 2. 实时行情
def t2():
    q=asyncio.run(get_realtime_quote('603002'))
    assert q.get('price'),'无价格'
    print(f'  {q["name"]}: ¥{q["price"]} ({q["change_pct"]:+.2f}%)')

# 3. K线
def t3():
    k=asyncio.run(get_kline('603002',10))
    assert k['count']>=5
    print(f'  {k["count"]}条, last={k["data"][-1]["date"]}')

# 4. 技术
def t4():
    t=asyncio.run(get_technical('603002',60))
    v=t['latest_values']
    assert v.get('MA5')
    print(f'  MA5={v["MA5"]:.2f} DIF={v["DIF"]:.4f} RSI6={v.get("RSI6"):.1f}')

# 5. 估值(可能空,不报错即过)
def t5():
    v=asyncio.run(get_valuation('603002'))
    print(f'  items={len(v.get("data",{}))}')

# 6. 财务(可能部分空,不报错即过)
def t6():
    f=asyncio.run(get_financial('603002'))
    l=f.get('latest')
    print(f'  latest={l}, history={len(f.get("history",[]))}')

# 7. 资金(可能空,不报错即过)
def t7():
    ff=asyncio.run(get_fund_flow('603002',5))
    print(f'  {len(ff.get("data",[]))}条{" (不可用)" if ff.get("_unavailable") else ""}')

# 8. 分析(必须返回有效分数)
def t8():
    a=asyncio.run(get_investment_analysis('603002'))
    assert a['total_score'] is not None
    assert 0<=a['total_score']<=100
    print(f'  总分:{a["total_score"]} | {a["recommendation"][:20]}...')
    for k,v in a.get('dimensions',{}).items():
        print(f'    {k}:{v["score"]}分')

# 9. 市场
def t9():
    m=asyncio.run(get_market_overview())
    print(f'  indices={len(m["indices"])} sectors={len(m["top_sectors"])} gainers={len(m["top_gainers"])}')
    if m['errors']:
        print(f'  errors={m["errors"]}')

# 10. API端点
def t10():
    from fastapi.testclient import TestClient
    from main import app
    c=TestClient(app)
    assert c.get('/health').status_code==200
    r=c.get('/api/v1/stocks/search?keyword=603002&limit=3')
    assert r.status_code==200
    d=r.json()
    assert d['count']>0
    print(f'  search:{d["results"][0]["name"]}')
    r=c.get('/api/v1/stocks/603002/realtime')
    assert r.status_code==200
    print(f'  realtime: OK (status={r.status_code})')
    r=c.get('/api/v1/stocks/603002/analysis')
    assert r.status_code==200
    a=r.json()
    print(f'  analysis: score={a["total_score"]}')
    r=c.get('/api/v1/market/overview')
    assert r.status_code==200
    print(f'  market: OK (status={r.status_code})')

if __name__=='__main__':
    for tfn in [t1,t2,t3,t4,t5,t6,t7,t8,t9,t10]:
        t(tfn.__doc__ or tfn.__name__,tfn)
    print(f'\n{"="*40}')
    print(f'结果: {10-len(FAILS)}/10 通过')
    if FAILS:
        print(f'失败项: {FAILS}')
    else:
        print('ALL PASSED')
