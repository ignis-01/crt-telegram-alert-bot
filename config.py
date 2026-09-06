import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    twelve_key: str = os.getenv("TWELVE_DATA_API_KEY", "")
    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    scan_seconds: int = int(os.getenv("SCAN_SECONDS", "60"))
    cooldown_minutes: int = int(os.getenv("ALERT_COOLDOWN_MINUTES", "240"))
    lookback: int = int(os.getenv("LOOKBACK", "250"))

    symbols = {
        # Major FX pairs
        "EURUSD": "EUR/USD",
        "GBPUSD": "GBP/USD",
        "USDJPY": "USD/JPY",
        "USDCHF": "USD/CHF",
        "AUDUSD": "AUD/USD",
        "USDCAD": "USD/CAD",
        "NZDUSD": "NZD/USD",

        # Metals + crypto
        "XAUUSD": "XAU/USD",
        "XAGUSD": "XAG/USD",
        "BTCUSD": "BTC/USD",
    }

    def validate(self):
        missing = []
        if not self.twelve_key:
            missing.append("TWELVE_DATA_API_KEY")
        if not self.telegram_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if missing:
            raise RuntimeError("Missing: " + ", ".join(missing))
