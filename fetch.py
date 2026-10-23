#!/usr/bin/env python3
"""撈美股指數（Yahoo Finance）與台指期夜盤（期交所行情），寫成 data.json。
用法：python3 fetch.py [輸出路徑]，不給路徑就印到螢幕。只用標準函式庫。"""
import json, sys, time, urllib.request
from datetime import datetime, timezone, timedelta

TPE = timezone(timedelta(hours=8))
UA = {"User-Agent": "Mozilla/5.0"}
US = [("^DJI", "道瓊工業"), ("^GSPC", "S&P 500"), ("^IXIC", "那斯達克"), ("^SOX", "費城半導體")]


def get(url, body=None):
    h = dict(UA)
    if body is not None:
        h["Content-Type"] = "application/json"
        body = json.dumps(body).encode()
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, body, h), timeout=20) as r:
                return json.load(r)
        except Exception:
            if i == 2:
                raise
            time.sleep(3)


def us_index(sym, name):
    r = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(sym)}?range=1mo&interval=1d")["chart"]["result"][0]
    pts = [(t, c) for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c is not None]
    m = r["meta"]
    last = m.get("regularMarketPrice") or pts[-1][1]
    prev = pts[-2][1] if len(pts) > 1 else last
    t = datetime.fromtimestamp(m.get("regularMarketTime") or pts[-1][0], TPE)
    return {
        "symbol": sym, "name": name, "last": round(last, 2),
        "change": round(last - prev, 2), "pct": round((last - prev) / prev * 100, 2),
        "high": m.get("regularMarketDayHigh"), "low": m.get("regularMarketDayLow"),
        "time": t.strftime("%Y-%m-%d %H:%M"),
        "spark": [round(c, 2) for _, c in pts[-22:]],
    }


def taifex(market):
    # market: "1" = 夜盤（盤後）, "0" = 日盤
    d = get("https://mis.taifex.com.tw/futures/api/getQuoteList", {
        "MarketType": market, "SymbolType": "F", "KindID": "1", "CID": "TXF",
        "ExpireMonth": "", "RowSize": "全部", "PageNo": "", "SortColumn": "", "AscDesc": "A"})
    suffix = "-M" if market == "1" else "-F"
    q = next(x for x in d["RtData"]["QuoteList"] if x["SymbolID"].endswith(suffix))  # 第一筆就是近月
    f = lambda k: float(q[k]) if q.get(k) not in ("", None) else None
    d8, t6 = q["CDate"], (q["CTime"] or "000000").zfill(6)
    return {
        "name": q["DispCName"], "contract": q["SymbolID"], "last": f("CLastPrice"),
        "ref": f("CRefPrice"), "change": f("CDiff"), "pct": f("CDiffRate"),
        "open": f("COpenPrice"), "high": f("CHighPrice"), "low": f("CLowPrice"),
        "volume": int(q["CTotalVolume"] or 0), "date": f"{d8[:4]}-{d8[4:6]}-{d8[6:]}",
        "time": f"{t6[:2]}:{t6[2:4]}",
    }


def main():
    out = {"updated": datetime.now(TPE).strftime("%Y-%m-%d %H:%M"), "us": [], "tw": {}, "errors": []}
    for sym, name in US:
        try:
            out["us"].append(us_index(sym, name))
        except Exception as e:
            out["errors"].append(f"{name}: {e}")
    for key, market in (("night", "1"), ("day", "0")):
        try:
            out["tw"][key] = taifex(market)
        except Exception as e:
            out["errors"].append(f"台指期{key}: {e}")
    s = json.dumps(out, ensure_ascii=False, indent=1)
    if len(sys.argv) > 1:
        open(sys.argv[1], "w", encoding="utf-8").write(s)
    else:
        print(s)
    return 0 if out["us"] or out["tw"] else 1


if __name__ == "__main__":
    sys.exit(main())
