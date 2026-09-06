import requests
import pandas as pd

URL = "https://api.twelvedata.com/time_series"

INTERVALS = {"15m": "15min", "4h": "4h", "1d": "1day"}

def fetch_ohlc(api_key, symbol, interval, outputsize=250):
    r = requests.get(
        URL,
        params={
            "symbol": symbol,
            "interval": INTERVALS[interval],
            "outputsize": outputsize,
            "apikey": api_key,
            "timezone": "UTC",
            "format": "JSON",
        },
        timeout=20,
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("status") != "ok":
        raise RuntimeError(str(payload))

    df = pd.DataFrame(payload["values"])
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values("datetime").set_index("datetime")[["open","high","low","close"]].dropna()
