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
        smart_wallets = [w for w, c in wallet_activity.items() if c >= 3]
        return smart_wallets, txns
    except Exception as e:
        print(f"smart_money error: {e}")
        return [], []

def check_new_tokens(txns, smart_wallets):
    smart_set = set(smart_wallets)
    alerts = []
    for tx in txns:
        fp = tx.get("feePayer", "")
        transfers = tx.get("tokenTransfers", [])
        for t in transfers:
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
            is_smart = fp in smart_set
            alerts.append({"mint": mint, "wallet": fp, "amount": amt, "smart": is_smart, "sig": tx.get("signature", "")[:12]})
    return alerts

def check_dexscreener():
    try:
        res = requests.get("https://api.dexscreener.com/token-boosts/top/v1", timeout=10)
        data = res.json()
        alerts = []
        for item in data[:5]:
            mint = item.get("tokenAddress", "")
            chain = item.get("chainId", "")
            if chain != "solana" or not mint:
                continue
            key = f"dex_{mint}"
            if key in seen:
                continue
            seen.add(key)
            alerts.append({"mint": mint, "url": item.get("url", ""), "desc": item.get("description", "ミームコイン急上昇中")})
        return alerts
    except Exception as e:
        print(f"dexscreener error: {e}")
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
        if count >= 5:
            key = f"spike_{mint}"
            if key not in seen:
                seen.add(key)
                spikes.append({"mint": mint, "count": count})
    return spikes

def run():
    print("🚀 起動中...")
    send("🚀 <b>Meme Signal Bot が起動しました！</b>\nSolanaのミームコインシグナルを監視中...")
    while True:
        try:
            smart_wallets, txns = check_smart_money()
            if smart_wallets:
                for a in check_new_tokens(txns, smart_wallets):
                    tag = "🧠 <b>Smart Money購入！</b>" if a["smart"] else "🆕 <b>新規トークン検出</b>"
                    send(f"{tag}\n\n📍 Mint: <code>{a['mint'][:20]}...</code>\n👛 Wallet: <code>{a['wallet'][:12]}...</code>\n💰 数量: {a['amount']:,.0f}\n📊 <a href='https://dexscreener.com/solana/{a['mint']}'>DexScreenerで確認</a>\n\n⚠️ リスク高（ミームコイン）")
            for s in check_liquidity_spike(txns):
                send(f"💧 <b>流動性急増！</b>\n\n📍 Mint: <code>{s['mint'][:20]}...</code>\n🔥 直近取引数: {s['count']}件\n📊 <a href='https://dexscreener.com/solana/{s['mint']}'>DexScreenerで確認</a>\n\n⚠️ リスク高（ミームコイン）")
            for d in check_dexscreener():
                send(f"📈 <b>DexScreenerトレンド急上昇！</b>\n\n📍 Mint: <code>{d['mint'][:20]}...</code>\n📝 {d['desc']}\n🔗 <a href='{d['url']}'>詳細を見る</a>\n\n⚠️ リスク高（ミームコイン）")
        except Exception as e:
            print(f"エラー: {e}")
        time.sleep(20)

if __name__ == "__main__":
    run()
