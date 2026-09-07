# Dray CRT Telegram Alert Bot

Alert-only scanner for the Daily -> 4H -> 15M CRT workflow.

Markets: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD, XAU/USD, XAG/USD, BTC/USD.

The current detector is a mechanical prototype. It must be backtested against your exact CRT training rules before you rely on its alerts.

Environment variables:
- TWELVE_DATA_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID (optional; if blank, the bot waits for /start and discovers it)
- SCAN_SECONDS (default 60)
- ALERT_COOLDOWN_MINUTES (default 240)
- LOOKBACK (default 250)

Render:
- Service type: Background Worker
- Build: pip install -r requirements.txt
- Start: python main.py


## Easier Telegram setup

If TELEGRAM_CHAT_ID is left blank, deploy the worker and send `/start` to your bot.
The worker will detect the chat ID and send a connection confirmation.
You can then optionally save that ID as TELEGRAM_CHAT_ID.


## Updated CRT logic
The alert key level is now a Daily Order Block. The sequence is: Daily rejection -> Daily OB reaction -> 4H internal/external closed-candle breakout -> 15M TBS -> Model #1 -> alert when price is at the Daily OB. This is a mechanical implementation of the supplied rules and should be backtested before live use.
