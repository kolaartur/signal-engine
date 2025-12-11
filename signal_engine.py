import requests
import json
import time

# -------------------------------------------------
# Telegram details (your real values)
# -------------------------------------------------
BOT_TOKEN = "8590902045:AAE2MX1b-uolvdfKvsicu5Sp-zbtJfNFw8c"
CHAT_ID = "-1003486964840"   # your channel/group ID

# -------------------------------------------------
# APIs for live prices
# -------------------------------------------------
API_URLS = {
    "BTCUSD": "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
    "XAUUSD": "https://www.goldapi.io/api/XAU/USD",
    "US500": "https://financialmodelingprep.com/api/v3/quote/%5EGSPC",
    "US100": "https://financialmodelingprep.com/api/v3/quote/%5EIXIC",
    "US30": "https://financialmodelingprep.com/api/v3/quote/%5EDJI",
    "USOIL": "https://api.finage.co.uk/last/forex/USOIL/USD"
}

# -------------------------------------------------
# Send Telegram message
# -------------------------------------------------
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload)

# -------------------------------------------------
# Get price from URL
# -------------------------------------------------
def get_price(url):
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        return list(data.values())[1] if isinstance(data, dict) else data[0]["price"]
    except:
        return "Error"

# -------------------------------------------------
# Startup message
# -------------------------------------------------
send_message("🔥 Bot started on Render successfully!")

# -------------------------------------------------
# Main loop
# -------------------------------------------------
while True:
    message = "📡 Live Prices:\n"
    for symbol, url in API_URLS.items():
        price = get_price(url)
        message += f"{symbol}: {price}\n"

    send_message(message)
    time.sleep(30)
