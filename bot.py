import os
import time
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

seen = set()

def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def get_name(mint):
    try:
        res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{mint}", timeout=8)
        pairs = res.json().get("pairs", [])
        if pairs:
            b = pairs[0].get("baseToken", {})
            return f"{b.get('name','')} (${b.get('symbol','')})"
    except:
        pass
    return "不明"

def run():
    send("🚀 Bot起動！10分ごとに通知します")
    while True:
        try:
            res = requests.get("https://api.dexscreener.com/token-boosts/top/v1", timeout=10)
            for item in res.json()[:5]:
                mint = item.get("tokenAddress", "")
                if item.get("chainId") != "solana" or not mint or mint in seen:
                    continue
                seen.add(mint)
                name = get_name(mint)
                send(
                    f"📈 <b>トレンド急上昇！</b>\n\n"
                    f"🪙 <b>{name}</b>\n"
                    f"🔗 <a href='https://gmgn.ai/sol/token/{mint}'>GMGNで確認</a>\n"
                    f"⚠️ リスク高"
                )
                time.sleep(3)
        except Exception as e:
            print(e)
        time.sleep(600)

if __name__ == "__main__":
    run()
