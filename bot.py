import os
import time
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")

seen = set()

def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def get_token_name(mint):
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
    print("起動中...")
    send("🚀 <b>Meme Signal Bot 起動！</b>")

    while True:
        try:
            res = requests.get("https://api.dexscreener.com/token-boosts/top/v1", timeout=10)
            items = res.json()
            new_count = 0
            for item in items:
                mint = item.get("tokenAddress", "")
                chain = item.get("chainId", "")
                if chain != "solana" or not mint:
                    continue
                if mint in seen:
                    continue
                seen.add(mint)
                new_count += 1
                name = get_token_name(mint)
                gmgn = f"https://gmgn.ai/sol/token/{mint}"
                dex = f"https://dexscreener.com/solana/{mint}"
                send(
                    f"📈 <b>トレンド急上昇！</b>\n\n"
                    f"🪙 銘柄: <b>{name}</b>\n"
                    f"🔗 <a href='{gmgn}'>GMGNで確認</a>  |  <a href='{dex}'>DexScreener</a>\n\n"
                    f"⚠️ リスク高（ミームコイン）"
                )
                time.sleep(2)

            print(f"チェック完了 新規{new_count}件 次は10分後")

        except Exception as e:
            print(f"エラー: {e}")

        # 10分待つ
        time.sleep(600)

if __name__ == "__main__":
    run()
