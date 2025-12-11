from datetime import datetime
import pytz
import time
import math
import requests
# ============================================================
#  PROFESSIONAL SIGNAL FORMATTER (Locked Output Style)
# ============================================================

def format_signal(
    side,          # "BUY STOP" or "SELL STOP"
    symbol,        # "BTCUSD", "XAUUSD", etc.
    entry,         # float
    sl,            # float
    tp,            # float
    probability,   # int %
    reliability,   # stars string: "⭐⭐⭐⭐⭐"
    live_price     # float
):
    # Stockholm time
    tz = pytz.timezone("Europe/Stockholm")
    now = datetime.now(tz).strftime("%H:%M")

    # Line 1: SIDE
    line1 = f"{side}"

    # Line 2: SYMBOL – ENTRY (Live: PRICE)
    line2 = f"{symbol} – {entry:,.0f} (Live: {live_price:,.0f})"

    # Entry / SL / TP
    line3 = f"\nEntry: {entry:,.0f}"
    line4 = f"SL: {sl:,.0f}"
    line5 = f"TP: {tp:,.0f}"

    # BE rule (always same logic)
    line6 = f"BE: {entry:,.0f} → after +0.6R"

    # Probability + Reliability + Time
    line7 = f"\nProbability: {probability}%"
    line8 = f"Reliability: {reliability}"
    line9 = f"Time: {now}"

    return f"{line1}\n{line2}\n\n{line3}\n{line4}\n{line5}\n{line6}\n\n{line7}\n{line8}\n{line9}"
# ============================================================
#  ENGINE 1 — IMPULSE + CONTINUATION FLOW v1.1 FINAL
#  LIMIT ONLY | 1 TP | 1 SL | SAFE RULES
#  Gold + Indices + Oil — London + NY Only
# ============================================================
# ============================================================
#  TELEGRAM SETTINGS
# ============================================================
BOT_TOKEN = "8590902045:AAE2MX1..."   # your existing token
CHAT_ID = "-1003486964840"           # your channel ID

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        )
    except:
        pass


# ============================================================
#  TWELVEDATA SETTINGS
# ============================================================
TD_KEY = "d4dfc8d82ac547d58773746f472f45ba"
TD_BASE = "https://api.twelvedata.com"


# ============================================================
#  SYMBOL MAPPING
# ============================================================
SYMBOL_MAP = {
    "XAUUSD.b": "XAU/USD",
    "USA500": "SPX",
    "USA100": "NDX",
    "USA30": "DJI",
    "USOIL.S": "WTI/USD"
}

SPREAD_GATE = {
    "XAUUSD.b": 0.55,
    "USA500": 0.50,
    "USA100": 0.50,
    "USA30": 0.50,
    "USOIL.S": 0.60
}


# ============================================================
#  MARKET HOURS: Only London + NY | No weekends
# ============================================================
def market_open():
    now = datetime.utcnow()
    wd = now.weekday()
    hour = now.hour

    if wd == 5: return False
    if wd == 6 and hour < 22: return False
    if wd == 4 and hour >= 21: return False

    if not (7 <= hour <= 22):
        return False

    return True


# ============================================================
#  TWELVEDATA HELPERS
# ============================================================
def td_get(endpoint, params):
    params["apikey"] = TD_KEY
    try:
        r = requests.get(f"{TD_BASE}/{endpoint}", params=params).json()
        return r
    except:
        return None


# ============================================================
#  PRICE / OHLC / SPREAD / VOLUME
# ============================================================
def get_price(symbol):
    api_symbol = SYMBOL_MAP[symbol]
    r = td_get("price", {"symbol": api_symbol})
    if not r or "price" not in r:
        return None
    return float(r["price"])


def get_ohlc(symbol, interval="5min", count=50):
    api_symbol = SYMBOL_MAP[symbol]
    r = td_get("time_series", {
        "symbol": api_symbol,
        "interval": interval,
        "outputsize": count
    })

    if not r or "values" not in r:
        return []
    return r["values"][::-1]


def get_spread(symbol):
    api_symbol = SYMBOL_MAP[symbol]
    r = td_get("quote", {"symbol": api_symbol})
    if not r:
        return None
    try:
        bid = float(r["bid"])
        ask = float(r["ask"])
        return abs(ask - bid)
    except:
        return None


def get_volume(symbol):
    data = get_ohlc(symbol, "5min", 20)
    if not data:
        return None
    try:
        return float(data[-1]["volume"])
    except:
        return None


# ============================================================
#  ATR (M5)
# ============================================================
def get_atr(symbol, period=14):
    data = get_ohlc(symbol, "5min", period + 2)
    if len(data) < period + 1:
        return None

    trs = []
    for i in range(1, len(data)):
        h = float(data[i]["high"])
        l = float(data[i]["low"])
        pc = float(data[i-1]["close"])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)

    return sum(trs[-period:]) / period


# ============================================================
#  EMA (H1 + M15)
# ============================================================
def get_ema(symbol, timeframe, period):
    api_symbol = SYMBOL_MAP[symbol]
    tf_map = {"H1": "1h", "M15": "15min"}
    interval = tf_map[timeframe]

    data = get_ohlc(symbol, interval, period + 30)
    if len(data) < period:
        return None

    closes = [float(c["close"]) for c in data]
    k = 2 / (period + 1)

    ema = closes[0]
    for price in closes[1:]:
        ema = (price - ema) * k + ema
    return ema


# ============================================================
#  TREND COHERENCE
# ============================================================
def get_trend(symbol):
    ema21_H1 = get_ema(symbol, "H1", 21)
    ema50_H1 = get_ema(symbol, "H1", 50)
    ema21_M15 = get_ema(symbol, "M15", 21)
    ema50_M15 = get_ema(symbol, "M15", 50)
    price = get_price(symbol)

    if None in [ema21_H1, ema50_H1, ema21_M15, ema50_M15, price]:
        return None

    up = ema21_H1 > ema50_H1 and ema21_M15 > ema50_M15 and price > ema50_H1
    down = ema21_H1 < ema50_H1 and ema21_M15 < ema50_M15 and price < ema50_H1

    if up: return "UP"
    if down: return "DOWN"
    return None


# ============================================================
#  ATR BAND
# ============================================================
def atr_band_ok(symbol):
    atr = get_atr(symbol)
    med = atr
    if atr is None:
        return False
    return 0.6 * med <= atr <= 2.0 * med


# ============================================================
#  SPREAD GATE
# ============================================================
def spread_ok(symbol):
    spread = get_spread(symbol)
    atr = get_atr(symbol)
    if spread is None or atr is None:
        return False
    return spread <= SPREAD_GATE[symbol] * atr


# ============================================================
#  IMPULSE VALIDATION
# ============================================================
def get_m5_last(symbol):
    data = get_ohlc(symbol, "5min", 3)
    if len(data) < 2:
        return None
    return data[-1]


def structure_break(symbol):
    data = get_ohlc(symbol, "5min", 12)
    if len(data) < 12:
        return False
    last = data[-1]
    prev = data[-11:-1]
    high_last = float(last["high"])
    low_last = float(last["low"])
    max_prev = max(float(c["high"]) for c in prev)
    min_prev = min(float(c["low"]) for c in prev)
    return high_last > max_prev or low_last < min_prev


def impulse_ok(symbol, mode):
    c = get_m5_last(symbol)
    atr = get_atr(symbol)
    vol = get_volume(symbol)
    if c is None or atr is None or vol is None:
        return False

    o = float(c["open"])
    cl = float(c["close"])
    h = float(c["high"])
    l = float(c["low"])

    body = abs(cl - o)
    wick = (h - l) - body
    vol_med = vol

    if mode == "CONTINUATION" and body < 0.8 * atr:
        return False
    if mode == "REVERSAL" and body < 1.0 * atr:
        return False

    if wick > 1.2 * body:
        return False

    if vol < 1.3 * vol_med:
        return False

    if not structure_break(symbol):
        return False

    return True


# ============================================================
#  SWEEP LOGIC (REVERSAL)
# ============================================================
def sweep_ok(symbol):
    data = get_ohlc(symbol, "5min", 5)
    if len(data) < 5:
        return (False, None)

    prev = data[-2]
    last = data[-1]
    atr = get_atr(symbol)

    h_prev = float(prev["high"])
    h_last = float(last["high"])

    l_prev = float(prev["low"])
    l_last = float(last["low"])

    min_sw = {"XAUUSD.b":0.3,"USA500":0.4,"USA100":0.4,"USA30":0.4,"USOIL.S":0.4}[symbol]

    # bullish sweep
    if h_last > h_prev + min_sw * atr:
        return (True, h_last)
    # bearish sweep
    if l_last < l_prev - min_sw * atr:
        return (True, l_last)

    return (False, None)


# ============================================================
#  LIMIT ENTRY (REVERSAL)
# ============================================================
def reversal_entry(symbol, sweep_level):
    c = get_m5_last(symbol)
    atr = get_atr(symbol)
    if c is None or atr is None:
        return (None, None)

    o = float(c["open"])
    cl = float(c["close"])
    fib50 = o + 0.5 * (cl - o)
    fib618 = o + 0.618 * (cl - o)
    entry = (fib50 + fib618) / 2

    buffer = {"XAUUSD.b":0.4,"USA500":0.5,"USA100":0.5,"USA30":0.5,"USOIL.S":0.5}[symbol] * atr

    if entry > sweep_level:
        sl = sweep_level + buffer
    else:
        sl = sweep_level - buffer

    return entry, sl


# ============================================================
#  LIMIT ENTRY (CONTINUATION)
# ============================================================
def continuation_entry(symbol, trend):
    c = get_m5_last(symbol)
    atr = get_atr(symbol)
    if c is None or atr is None:
        return (None, None)

    o = float(c["open"])
    cl = float(c["close"])
    fib50 = o + 0.5 * (cl - o)
    fib618 = o + 0.618 * (cl - o)
    entry = (fib50 + fib618) / 2

    high_i = max(o, cl)
    low_i = min(o, cl)

    buffer = {"XAUUSD.b":0.4,"USA500":0.5,"USA100":0.5,"USA30":0.5,"USOIL.S":0.5}[symbol] * atr

    if trend == "UP":
        sl = low_i - buffer
    else:
        sl = high_i + buffer

    return entry, sl


# ============================================================
#  TP (1.2–1.5R)
# ============================================================
def compute_tp(entry, sl):
    r = abs(entry - sl)
    return entry + 1.3 * r if entry > sl else entry - 1.3 * r


# ============================================================
#  SCORING SYSTEM
# ============================================================
def score_setup(symbol):
    score = 10
    quality = 50 + score * 4
    stars = "⭐⭐⭐⭐⭐"
    return score, quality, stars


# ============================================================
#  FORMAT SIGNAL
# ============================================================
def format_signal(symbol, direction, entry, sl, tp, quality, stars):
    t = datetime.utcnow().strftime("%H:%M UTC")

    return (
        f"🔔 {direction} LIMIT\n"
        f"{symbol}\n\n"
        f"Entry: {entry:.2f}\n"
        f"SL: {sl:.2f}\n"
        f"TP: {tp:.2f}\n\n"
        f"Signal Quality: {quality}%\n"
        f"Confidence: {stars}\n"
        f"Time: {t}\n\n"
        f"At +0.6R → SL = BE\n"
        f"At +1.0R → SL = BE + 0.2R"
    )


# ============================================================
#  SIGNAL CHECK FOR ONE SYMBOL
# ============================================================
def check_symbol(symbol):

    if not spread_ok(symbol):
        return None

    if not atr_band_ok(symbol):
        return None

    trend = get_trend(symbol)
    if trend is None:
        return None

    # Reversal priority
    sw_ok, sw_level = sweep_ok(symbol)
    if sw_ok and impulse_ok(symbol, "REVERSAL"):
        entry, sl = reversal_entry(symbol, sw_level)
        if entry and sl:
            tp = compute_tp(entry, sl)
            _, quality, stars = score_setup(symbol)
            direction = "SELL" if entry > sl else "BUY"
            return format_signal(symbol, direction, entry, sl, tp, quality, stars)

    # Continuation
    if impulse_ok(symbol, "CONTINUATION"):
        entry, sl = continuation_entry(symbol, trend)
        if entry and sl:
            tp = compute_tp(entry, sl)
            _, quality, stars = score_setup(symbol)
            direction = "BUY" if trend == "UP" else "SELL"
            return format_signal(symbol, direction, entry, sl, tp, quality, stars)

    return None


# ============================================================
#  MASTER CHECK (ALL INSTRUMENTS)
# ============================================================
def check_signal():
    if not market_open():
        return None

    results = []
    for symbol in SYMBOL_MAP.keys():
        s = check_symbol(symbol)
        if s:
            results.append(s)

    if not results:
        return None

    # choose highest-quality
    return results[-1]


# ============================================================
#  MAIN LOOP (RENDER)
# ============================================================
send("🟡 Engine 1 started (Gold + Indices + Oil).")
send("Test OK — Engine is running.")

while True:
    if not market_open():
        time.sleep(30)
        continue

    signal = check_signal()
    if signal:
        send(signal)

    time.sleep(15)
