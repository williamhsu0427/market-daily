#!/usr/bin/env python3
"""讀 data.json，把早報用 LINE Messaging API 推給自己。
需要環境變數 LINE_TOKEN（channel access token）與 LINE_USER_ID；沒設就只印出內容。"""
import json, os, sys, urllib.request


def arrow(x):
    return "🔺" if x > 0 else "🔻" if x < 0 else "➖"


def build(d):
    lines = [f"📈 美股台指早報（{d['updated'][:10]}）", ""]
    n = (d.get("tw") or {}).get("night")
    if n:
        lines += [f"【台指期夜盤】{n['date'][5:]}",
                  f"{arrow(n['change'])} {n['last']:,.0f}  {n['change']:+,.0f}（{n['pct']:+.2f}%）",
                  f"高 {n['high']:,.0f}／低 {n['low']:,.0f}／量 {n['volume']:,} 口", ""]
    lines.append("【美股】")
    for x in d.get("us", []):
        lines.append(f"{arrow(x['change'])} {x['name']} {x['last']:,.2f}（{x['pct']:+.2f}%）")
    if d.get("errors"):
        lines += ["", "⚠️ 部分資料抓取失敗"]
    lines += ["", "https://williamhsu0427.github.io/market-daily/app/"]
    return "\n".join(lines)


def main():
    d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "data.json", encoding="utf-8"))
    text = build(d)
    token, uid = os.environ.get("LINE_TOKEN"), os.environ.get("LINE_USER_ID")
    if not token or not uid:
        print(text)
        print("\n（沒有設定 LINE_TOKEN / LINE_USER_ID，未發送）")
        return 0
    body = json.dumps({"to": uid, "messages": [{"type": "text", "text": text}]}).encode()
    req = urllib.request.Request("https://api.line.me/v2/bot/message/push", body, {
        "Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        print("LINE 已發送", r.status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
