from dataclasses import dataclass

@dataclass
class CRTSetup:
    direction: str
    crth: float
    crtl: float
    midpoint: float
    rejection: str
    breakout: str
    trigger: str
    ob_direction: str
    ob_low: float
    ob_high: float
    price: float

def mid(high, low):
    return (high + low) / 2.0

def daily_range(df):
    candle = df.iloc[-2]  # most recently CLOSED Daily candle
    return float(candle.high), float(candle.low), candle

def daily_rejection(candle, crth, crtl):
    # Price reaches an extreme and closes back inside the CRT range.
    if candle.high >= crth and candle.close < crth:
        return "BEARISH"
    if candle.low <= crtl and candle.close > crtl:
        return "BULLISH"
    return None

def find_daily_order_block(df, direction, lookback=30):
    # Conservative OB: opposite candle immediately before displacement.
    if len(df) < 10:
        return None
    work = df.iloc[-(lookback + 5):-1]
    for i in range(len(work) - 2, 2, -1):
        c = work.iloc[i]
        nxt = work.iloc[i + 1]
        prior = work.iloc[i - 3:i]

        if direction == "BULLISH":
            opposite = c.close < c.open
            displacement = nxt.close > nxt.open and nxt.close > prior.high.max()
        else:
            opposite = c.close > c.open
            displacement = nxt.close < nxt.open and nxt.close < prior.low.min()

        if opposite and displacement:
            return {"low": float(c.low), "high": float(c.high)}
    return None

def h4_breakout(df, daily_ob, lookback=6):
    # Internal = closed beyond recent 4H swing but still inside Daily OB.
    # External = closed beyond the Daily OB boundary.
    # Wick-only breaks are ignored.
    if len(df) < lookback + 4:
        return None

    candle = df.iloc[-2]
    prior = df.iloc[-(lookback + 2):-2]

    if candle.close > prior.high.max():
        return "BULLISH_INTERNAL" if candle.close <= daily_ob["high"] else "BULLISH_EXTERNAL"

    if candle.close < prior.low.min():
        return "BEARISH_INTERNAL" if candle.close >= daily_ob["low"] else "BEARISH_EXTERNAL"

    return None

def tbs_15m(df, direction, crth, crtl):
    # TBS: sweep premium/discount, rejection wick, close back inside.
    if len(df) < 10:
        return None

    midpoint = mid(crth, crtl)
    work = df.iloc[-9:-1]

    for i in range(len(work) - 1, -1, -1):
        c = work.iloc[i]
        body = abs(c.close - c.open)
        upper_wick = c.high - max(c.open, c.close)
        lower_wick = min(c.open, c.close) - c.low

        if direction == "BEARISH":
            # Premium sweep and close back below 50%.
            if c.high >= midpoint and c.close < midpoint and upper_wick >= max(body * 0.75, 0):
                return {"index": c.name, "high": float(c.high), "low": float(c.low)}
        else:
            # Discount sweep and close back above 50%.
            if c.low <= midpoint and c.close > midpoint and lower_wick >= max(body * 0.75, 0):
                return {"index": c.name, "high": float(c.high), "low": float(c.low)}

    return None

def model_one_after_tbs(df, direction, tbs):
    # Model #1 confirmation candle must come after TBS.
    # Live price must break that confirmation candle.
    if not tbs:
        return None

    closed = df.iloc[:-1]
    try:
        pos = closed.index.get_loc(tbs["index"])
    except KeyError:
        return None

    if pos + 1 >= len(closed):
        return None

    model = closed.iloc[pos + 1]
    live = df.iloc[-1]

    if direction == "BEARISH":
        if model.close >= model.open:
            return None
        if live.low <= model.low:
            return "MODEL_1_SHORT"
    else:
        if model.close <= model.open:
            return None
        if live.high >= model.high:
            return "MODEL_1_LONG"

    return None

def price_in_ob(price, ob):
    return bool(ob and ob["low"] <= price <= ob["high"])

def scan(daily, h4, m15):
    # 1. Mandatory Daily rejection.
    crth, crtl, daily_candle = daily_range(daily)
    rejection = daily_rejection(daily_candle, crth, crtl)
    if not rejection:
        return None

    # 2. Daily Order Block is now the CRT key level.
    daily_ob = find_daily_order_block(daily, rejection)
    if not daily_ob:
        return None

    # Rejection must overlap the Daily OB.
    if daily_candle.high < daily_ob["low"] or daily_candle.low > daily_ob["high"]:
        return None

    # 3. Mandatory 4H internal/external breakout.
    breakout = h4_breakout(h4, daily_ob)
    if not breakout:
        return None

    direction = "BULLISH" if breakout.startswith("BULLISH") else "BEARISH"

    # 4. Trade only in the 4H breakout direction.
    if direction != rejection:
        return None

    # 5. 15M TBS.
    tbs = tbs_15m(m15, direction, crth, crtl)
    if not tbs:
        return None

    # 6. 15M Model #1.
    trigger = model_one_after_tbs(m15, direction, tbs)
    if not trigger:
        return None

    # 7. Price must be reacting at the Daily Order Block key level.
    price = float(m15.iloc[-1].close)
    if not price_in_ob(price, daily_ob):
        return None

    return CRTSetup(
        direction=direction,
        crth=crth,
        crtl=crtl,
        midpoint=mid(crth, crtl),
        rejection=rejection,
        breakout=breakout,
        trigger=trigger,
        ob_direction=direction,
        ob_low=daily_ob["low"],
        ob_high=daily_ob["high"],
        price=price,
    )
