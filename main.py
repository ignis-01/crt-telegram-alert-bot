import logging
import os
import time
from config import Config
from data import fetch_ohlc
from strategy import scan
from telegram import send_message

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
        f"Current price: {price(s.price)}\n"
        f"Signal ID: {s.signal_id}\n\n"
        "ALERT ONLY — verify the chart before acting."
    )


def main():
    cfg = Config()
    cfg.validate()

    if not cfg.telegram_chat_id:
        raise RuntimeError(
            "TELEGRAM_CHAT_ID is required for GitHub Actions. "
            "Add it as a GitHub Actions repository secret."
        )

    sent = 0
    request_delay = float(os.getenv("REQUEST_DELAY_SECONDS", "2"))

    logging.info("Dray CRT scheduled scan started")

    for label, symbol in cfg.symbols.items():
        try:
            logging.info("Scanning %s", label)
            d = fetch_ohlc(cfg.twelve_key, symbol, "1d", cfg.lookback)
            time.sleep(request_delay)
            h4 = fetch_ohlc(cfg.twelve_key, symbol, "4h", cfg.lookback)
            time.sleep(request_delay)
            m15 = fetch_ohlc(cfg.twelve_key, symbol, "15m", cfg.lookback)

            setup = scan(d, h4, m15)
            if not setup:
                logging.info("%s: no confirmed setup", label)
                continue

            # GitHub Actions is stateless between runs. The workflow itself
            # runs on a fixed schedule, so avoid duplicate alerts by storing
            # a deterministic signal fingerprint in the Telegram message and
            # using the optional state file only during a single run.
            send_message(cfg.telegram_token, cfg.telegram_chat_id, alert(label, setup))
            sent += 1
            logging.info("%s: Telegram alert sent", label)

        except Exception:
            logging.exception("%s: scan failed", label)

        time.sleep(request_delay)

    logging.info("Scheduled scan finished. Alerts sent: %d", sent)


if __name__ == "__main__":
    main()
