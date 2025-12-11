import requests
import json
import time

# -------------------------
# SETTINGS
# -------------------------

# Telegram
BOT_TOKEN = "8590902045:AAE2gxctR5xxsPUrwmisL_1zYKWQ2KgHqsZY"
CHAT_ID = "-1003486964840"

# APIs we use for live prices
API_URLS = {
    "BTCUSD": "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
    "XAUUSD": "https://metals-api.com/api/latest?access_key=demo&base=XAU&symbols=USD",
    "US500": "https://financialmodelingprep.com/api/v3/quote/%5EGSPC?apikey=demo",
    "US100": "https://financialmodelingprep.com/api/v3/quote/%5EIXIC?apikey=demo",
    "US30": "https://financialmodelingprep.com/api/v3/quote/%5EDJI?apikey=demo",
    "USOIL": "https://api.finage.co.uk/last/trade/CL?
