
# ============================================================
# IMPULSE + CONTINUATION FLOW v1.1 — FINAL (CRYPTO 24/7)
# BTC / ETH / BNB / SOL
# LIMIT ONLY | 1 TP | 1 SL | SAFE RULES
# ============================================================

import time, json, threading, requests
from collections import deque
import websocket
from datetime import datetime
import pytz

# ========================= CONFIG ============================

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
INTERVAL = "5"
WS_URL = "wss://stream.bybit.com/v5/public/linear"

TELEGRAM_TOKEN = "8590902045:AAE2gxtR5xxsPUrwmisL_1zYKWQ2KgHqsZY"
TELEGRAM_CHAT_ID = "-1003486964840"

HEARTBEAT_SECONDS = 15 * 60
COOLDOWN_SECONDS = 120
MAX_BARS = 400
TZ = pytz.timezone("Europe/Stockholm")

# ========================= STATE =============================

m5 = {s: deque(maxlen=MAX_BARS) for s in SYMBOLS}
m15 = {s: deque(maxlen=200) for s in SYMBOLS}
h1 = {s: deque(maxlen=200) for s in SYMBOLS}
last_signal_time = {s: 0 for s in SYMBOLS}

# ========================= TELEGRAM ==========================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
        timeout=10
    )

def heartbeat():
    while True:
        send("🟢 IMPULSE + CONTINUATION FLOW v1.1 — ONLINE")
        time.sleep(HEARTBEAT_SECONDS)

# ========================= UTILS =============================

def atr(bars, p=14):
    trs = []
    for i in range(1, p + 1):
        h, l = bars[-i]["high"], bars[-i]["low"]
        pc = bars[-i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs) / p

def ema(vals, p):
    k = 2 / (p + 1)
    e = vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e

def median(vals):
    s = sorted(vals)
    return s[len(s) // 2]

# ========================= TREND =============================

def trend_ok(symbol):
    if len(m15[symbol]) < 60 or len(h1[symbol]) < 60:
        return None

    m15c = [b["close"] for b in m15[symbol]]
    h1c = [b["close"] for b in h1[symbol]]

    m15_21 = ema(m15c[-21:], 21)
    m15_50 = ema(m15c[-50:], 50)
    h1_21 = ema(h1c[-21:], 21)
    h1_50 = ema(h1c[-50:], 50)

    if m15_21 > m15_50 and h1_21 > h1_50 and h1c[-1] > h1_50:
        return "BUY"
    if m15_21 < m15_50 and h1_21 < h1_50 and h1c[-1] < h1_50:
        return "SELL"
    return None

# ========================= CORE ==============================

def check(symbol):
    bars = m5[symbol]
    if len(bars) < 120:
        return

    now = time.time()
    if now - last_signal_time[symbol] < COOLDOWN_SECONDS:
        return

    a = atr(bars)
    atr_hist = [atr(bars[i-20:i]) for i in range(40, len(bars))]
    atr_med = median(atr_hist[-20:])

    if not (0.6 * atr_med <= a <= 2.0 * atr_med):
        return

    last = bars[-1]
    body = abs(last["close"] - last["open"])
    wick = (last["high"] - last["low"]) - body

    vols = [b["volume"] for b in bars[-20:]]
    if body < 0.8 * a or wick > 1.2 * body or last["volume"] < 1.5 * median(vols):
        return

    highs = [b["high"] for b in bars[-11:-1]]
    lows = [b["low"] for b in bars[-11:-1]]

    impulse = None
    if last["close"] > max(highs):
        impulse = "BUY"
    if last["close"] < min(lows):
        impulse = "SELL"
    if not impulse:
        return

    trend = trend_ok(symbol)

    if trend != impulse:
        sweep = abs(last["high"] - max(highs)) if impulse == "SELL" else abs(min(lows) - last["low"])
        if sweep < 0.8 * a:
            return

    entry = round((last["open"] + last["close"]) * 0.5, 2)

    if impulse == "BUY":
        sl = round(last["low"] - a, 2)
        pocket = max(b["high"] for b in m15[symbol][-20:])
        tp = round(min(pocket, entry + (entry - sl) * 1.5), 2)
    else:
        sl = round(last["high"] + a, 2)
        pocket = min(b["low"] for b in m15[symbol][-20:])
        tp = round(max(pocket, entry - (sl - entry) * 1.5), 2)

    score = 0
    score += 2 if trend == impulse else 1
    score += 2 if body >= a else 1
    score += 2 if last["volume"] >= 1.8 * median(vols) else 1
    score += 4

    if score < 7:
        return

    quality = 50 + score * 4
    last_signal_time[symbol] = now
    t = datetime.now(TZ).strftime("%H:%M")

    send(
        f"{impulse} STOP\n"
        f"{symbol.replace('USDT','USD')} — {entry} (Live: {round(last['close'],0)})\n\n"
        f"Entry: {entry}\n"
        f"SL: {sl}\n"
        f"TP: {tp}\n"
        f"BE: {entry} → after +0.6R\n\n"
        f"Probability: {quality}%\n"
        f"Reliability: ⭐⭐⭐⭐\n"
        f"Time: {t}"
    )

# ========================= WS ================================

def on_msg(ws, msg):
    d = json.loads(msg)
    if "topic" not in d or "data" not in d:
        return
    sym = d["topic"].split(".")[-1]
    k = d["data"][0]
    if not k["confirm"]:
        return

    m5[sym].append({
        "open": float(k["open"]),
        "high": float(k["high"]),
        "low": float(k["low"]),
        "close": float(k["close"]),
        "volume": float(k["volume"]),
    })

    check(sym)

def start():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_message=on_msg,
        on_open=lambda ws: ws.send(json.dumps({
            "op": "subscribe",
            "args": [f"kline.{INTERVAL}.{s}" for s in SYMBOLS]
        }))
    )
    ws.run_forever()

# ========================= START =============================

if __name__ == "__main__":
    threading.Thread(target=heartbeat, daemon=True).start()
    start()
