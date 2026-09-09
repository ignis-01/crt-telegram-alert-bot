# Dray CRT Telegram Alert Bot — GitHub Actions

Alert-only scanner for the Daily → 4H → 15M CRT workflow.

Markets: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD, XAU/USD, XAG/USD, BTC/USD.

The detector is a mechanical prototype. Backtest/validate it against your exact CRT rules before relying on alerts.

## GitHub Actions setup

This version runs as a scheduled, one-shot scan instead of a permanent server. The workflow is in `.github/workflows/crt-scan.yml` and runs every 5 minutes.

Add these as **GitHub repository Actions secrets**:

- `TWELVE_DATA_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Optional repository variable:

- `LOOKBACK` = `250`

Never put API keys or Telegram tokens directly in Python files, YAML, commits, or screenshots.

## Telegram chat ID

Start a chat with your Telegram bot and send `/start`. Then obtain the chat ID using Telegram's Bot API `getUpdates` endpoint or another trusted method, and save that number as the `TELEGRAM_CHAT_ID` GitHub secret. Never share your bot token publicly.

## How the workflow works

1. GitHub starts a fresh Ubuntu runner on schedule.
2. Python dependencies are installed.
3. The scanner fetches Daily, 4H and 15M OHLC data for each configured market.
4. The CRT detector checks Daily rejection → Daily Order Block → 4H internal/external breakout → 15M TBS → Model #1.
5. Confirmed setups are sent to Telegram.
6. The runner shuts down when the scan finishes.

Scheduled workflows run only from the repository's default branch. GitHub's shortest supported schedule interval is 5 minutes.
