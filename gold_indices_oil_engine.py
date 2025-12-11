import time
import requests
from datetime import datetime

# ---------------------------------------------------------------------------
#  Telegram Bot Settings
# ---------------------------------------------------------------------------
BOT_TOKEN = "8590902045:AAE2MX1..."   # your real token already
CHAT_ID = "-1003486964840"           # your real channel ID

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        )
    except:
        pass

# ---------------------------------------------------------------------------
#  Market Hours — Only Gold / Indices / Oil (NO crypto in this file)
# ---------------------------------------------------------------------------
def market_open():
    now = datetime.utcnow()
    wd = now.weekday()  # Monday = 0, Sunday = 6
    h = now.hour

    # Closed from Friday 21:00 UTC to Sunday 22:00 UTC
    if wd == 5:     # Saturday
        return False
    if wd == 6 and h < 22:  # Sunday before open
        return False
    if wd == 4 and h >= 21:  # Friday after 21:00
        return False

    return True

# ---------------------------------------------------------------------------
#  Dummy signal logic
# ---------------------------------------------------------------------------
def check_signal():
    return None  # No spam — logic added later


# ---------------------------------------------------------------------------
#  MAIN LOOP
# ---------------------------------------------------------------------------
send("🟡 Gold / Indices / Oil engine started.")

while True:
    if not market_open():
        time.sleep(30)
        continue

    signal = check_signal()

    if signal:
        send(signal)

    time.sleep(5)
