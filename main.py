import time
import logging
from config import Config
from data import fetch_ohlc
from strategy import scan
from telegram import send_message, wait_for_chat_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def price(v):
    return f"{v:.8f}".rstrip("0").rstrip(".")

def alert(symbol, s):
    side = "LONG 🟢" if s.direction == "BULLISH" else "SHORT 🔴"
    return (
        "🚨 CRT SETUP DETECTED\n\n"
        f"Symbol: {symbol}\n"
        f"Direction: {side}\n"
        "Framework: D → 4H → 15M\n\n"
        f"Daily rejection: {s.rejection}\n"
        f"4H breakout: {s.breakout}\n"
        f"15M trigger: {s.trigger}\n"
        f"Order Block: {s.ob_direction}\n"
        f"OB zone: {price(s.ob_low)} - {price(s.ob_high)}\n"
        f"CRT high: {price(s.crth)}\n"
        f"CRT 50%: {price(s.midpoint)}\n"
        f"CRT low: {price(s.crtl)}\n"
        f"Current price: {price(s.price)}\n\n"
        "ALERT ONLY — verify the chart before acting."
    )

def main():
    cfg = Config()
    cfg.validate()

    chat_id = cfg.telegram_chat_id
    if not chat_id:
        logging.info("Send /start to your Telegram bot now; discovering chat ID...")
        chat_id = wait_for_chat_id(cfg.telegram_token)

    sent = {}
    logging.info("Dray CRT scanner started")

    while True:
        for label, symbol in cfg.symbols.items():
            try:
                d = fetch_ohlc(cfg.twelve_key, symbol, "1d", cfg.lookback)
                h4 = fetch_ohlc(cfg.twelve_key, symbol, "4h", cfg.lookback)
                m15 = fetch_ohlc(cfg.twelve_key, symbol, "15m", cfg.lookback)
                setup = scan(d, h4, m15)

                if not setup:
                    logging.info("%s: no confirmed setup", label)
                    continue

                key = (label, setup.direction, setup.trigger, round(setup.ob_low, 8), round(setup.ob_high, 8))
                now = time.time()
                if now - sent.get(key, 0) < cfg.cooldown_minutes * 60:
                    continue

                send_message(cfg.telegram_token, chat_id, alert(label, setup))
                sent[key] = now
                logging.info("%s: Telegram alert sent", label)

            except Exception:
                logging.exception("%s: scan failed", label)

        time.sleep(cfg.scan_seconds)

if __name__ == "__main__":
    main()
