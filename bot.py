import os
import time
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")

RAYDIUM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
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
        data = res.json()
        pairs = data.get("pairs", [])
        if pairs:
            base = pairs[0].get("baseToken", {})
            name = base.get("name", "")
            symbol = base.get("symbol", "")
            if symbol:
                return f"{name} (${symbol})"
    except:
        pass
    return "不明"

def check_smart_money():
    try:
        url = f"https://api.helius.xyz/v0/addresses/{RAYDIUM}/transactions"
        params = {"api-key": HELIUS_API_KEY, "limit": 50, "type": "SWAP"}
        res = requests.get(url, params=params, timeout=15)
        txns = res.json()
        wallet_activity = {}
        for tx in txns:
            fp = tx.get("feePayer")
            if not fp:
                continue
            wallet_activity[fp] = wallet_activity.get(fp, 0) + 1
        # 5回以上に絞る（厳しく）
        smart_wallets = [w for w, c in wallet_activity.items() if c >= 5]
        return smart_wallets, txns
    except Exception as e:
        print(f"error: {e}")
        return [], []

def check_new_tokens(txns, smart_wallets):
    smart_set = set(smart_wallets)
    alerts = []
    for tx in txns:
        fp = tx.get("feePayer", "")
        # Smart Moneyのみ
        if fp not in smart_set:
            continue
        for t in tx.get("tokenTransfers", []):
            mint = t.get("mint", "")
            to = t.get("toUserAccount", "")
            amt = t.get("tokenAmount", 0)
            if mint in SKIP_MINTS or not mint:
                continue
            if to != fp:
                continue
            key = f"{fp}_{mint}"
            if key in seen:
                continue
            seen.add(key)
            alerts.append({"mint": mint, "wallet": fp, "amount": amt, "sig": tx.get("signature", "")[:12]})
    return alerts

def check_dexscreener():
    try:
        res = requests.get("https://api.dexscreener.com/token-boosts/top/v1", timeout=10)
        data = res.json()
        alerts = []
        for item in data[:3]:
            mint = item.get("tokenAddress", "")
            chain = item.get("chainId", "")
            if chain != "solana" or not mint:
                continue
            key = f"dex_{mint}"
            if key in seen:
                continue
            seen.add(key)
            alerts.append({"mint": mint, "url": item.get("url", ""), "desc": item.get("description", "")})
        return alerts
    except Exception as e:
        print(f"dex error: {e}")
        return []

def check_liquidity_spike(txns):
    mint_count = {}
    for tx in txns:
        for t in tx.get("tokenTransfers", []):
            mint = t.get("mint", "")
            if mint in SKIP_MINTS or not mint:
                continue
            mint_count[mint] = mint_count.get(mint, 0) + 1
    spikes = []
    for mint, count in mint_count.items():
        # 8件以上に絞る（厳しく）
        if count >= 8:
            key = f"spike_{mint}"
            if key not in seen:
                seen.add(key)
                spikes.append({"mint": mint, "count": count})
    return spikes

def run():
    print("起動中...")
    send("🚀 <b>Meme Signal Bot 起動！</b>\nSmart Moneyシグナルを監視中...")
    while True:
        try:
            smart_wallets, txns = check_smart_money()
            for a in check_new_tokens(txns, smart_wallets):
                name = get_token_name(a["mint"])
                send(
                    f"🧠 <b>Smart Money購入！</b>\n\n"
                    f"🪙 銘柄: <b>{name}</b>\n"
                    f"📍 Mint: <code>{a['mint'][:20]}...</code>\n"
                    f"👛 Wallet: <code>{a['wallet'][:12]}...</code>\n"
                    f"💰 数量: {a['amount']:,.0f}\n"
                    f"📊 <a href='https://dexscreener.com/solana/{a['mint']}'>DexScreenerで確認</a>\n\n"
                    f"⚠️ リスク高（ミームコイン）"
                )
            for s in check_liquidity_spike(txns):
                name = get_token_name(s["mint"])
                send(
                    f"💧 <b>流動性急増！</b>\n\n"
                    f"🪙 銘柄: <b>{name}</b>\n"
                    f"📍 Mint: <code>{s['mint'][:20]}...</code>\n"
                    f"🔥 直近取引数: {s['count']}件\n"
                    f"📊 <a href='https://dexscreener.com/solana/{s['mint']}'>DexScreenerで確認</a>\n\n"
                    f"⚠️ リスク高（ミームコイン）"
                )
            for d in check_dexscreener():
                name = get_token_name(d["mint"])
                send(
                    f"📈 <b>DexScreenerトレンド急上昇！</b>\n\n"
                    f"🪙 銘柄: <b>{name}</b>\n"
                    f"📍 Mint: <code>{d['mint'][:20]}...</code>\n"
                    f"🔗 <a href='{d['url']}'>詳細を見る</a>\n\n"
                    f"⚠️ リスク高（ミームコイン）"
                )
        except Exception as e:
            print(f"エラー: {e}")
        time.sleep(30)

if __name__ == "__main__":
    run()
