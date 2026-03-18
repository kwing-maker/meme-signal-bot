import os
import time
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")

SKIP_MINTS = {
    "So11111111111111111111111111111111111111112",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
}

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

    # DexScreenerトレンドのみを監視（一番信頼性高い）
    while True:
        try:
            res = requests.get("https://api.dexscreener.com/token-boosts/top/v1", timeout=10)
            items = res.json()
            for item in items:
                mint = item.get("tokenAddress", "")
                chain = item.get("chainId", "")
                if chain != "solana" or not mint:
                    continue
                if mint in seen:
                    continue
                seen.add(mint)
                name = get_token_name(mint)
                url = item.get("url", f"https://dexscreener.com/solana/{mint}")
                send(
                    f"📈 <b>トレンド急上昇！</b>\n\n"
                    f"🪙 銘柄: <b>{name}</b>\n"
                    f"🔗 <a href='{url}'>DexScreenerで確認</a>\n\n"
                    f"⚠️ リスク高（ミームコイン）"
                )
                time.sleep(3)
        except Exception as e:
            print(f"エラー: {e}")

        # 5分ごとにチェック
        time.sleep(300)

if __name__ == "__main__":
    run()
