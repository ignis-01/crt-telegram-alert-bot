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
    # Reference the most recently CLOSED Daily candle.
    candle = df.iloc[-2]
    return float(candle.high), float(candle.low), candle

def daily_rejection(candle, crth, crtl):
    # Mechanical prototype: wick tests an extreme and closes back inside.
    if candle.high >= crth and candle.close < crth:
        return "BEARISH"
    if candle.low <= crtl and candle.close > crtl:
        return "BULLISH"
    return None

def h4_breakout(df, lookback=5):
    # Mechanical prototype: last closed H4 candle closes beyond recent range.
    if len(df) < lookback + 3:
        return None
    candle = df.iloc[-2]
    prior = df.iloc[-(lookback+2):-2]
    if candle.close > prior.high.max():
        return "BULLISH_BREAKOUT"
    if candle.close < prior.low.min():
        return "BEARISH_BREAKOUT"
    return None

def order_block(df, direction, lookback=12):
    # Prototype OB: last opposite candle before a displacement close beyond a recent swing.
    if len(df) < lookback + 4:
        return None
    work = df.iloc[-(lookback+3):]
    for i in range(len(work)-2, 0, -1):
        c = work.iloc[i]
        nxt = work.iloc[i+1]
        prior = work.iloc[max(0, i-4):i]
        if prior.empty:
            continue
        if direction == "BULLISH":
            opposite = c.close < c.open
            displacement = nxt.close > nxt.open and nxt.close > prior.high.max()
        else:
            opposite = c.close > c.open
            displacement = nxt.close < nxt.open and nxt.close < prior.low.min()
        if opposite and displacement:
            return {"low": float(c.low), "high": float(c.high)}
    return None

def price_in_ob(price, ob):
    if not ob:
        return False
    return ob["low"] <= price <= ob["high"]

def model_one(df, direction, crth, crtl):
    # Prototype inspired by the supplied example:
    # sweep/rejection + correct side of 50%.
    if len(df) < 8:
        return None
    last = df.iloc[-2]
    recent = df.iloc[-7:-2]
    m = mid(crth, crtl)

    if direction == "BEARISH":
        sweep = max(float(recent.high.max()), float(last.high)) >= crth
        rejection = last.close < last.open or last.close < crth
        discount = last.close < m
        if sweep and rejection and discount:
            return "MODEL_1_SHORT"

    if direction == "BULLISH":
        sweep = min(float(recent.low.min()), float(last.low)) <= crtl
        rejection = last.close > last.open or last.close > crtl
        premium = last.close > m
        if sweep and rejection and premium:
            return "MODEL_1_LONG"

    return None

def scan(daily, h4, m15):
    crth, crtl, daily_candle = daily_range(daily)
    rejection = daily_rejection(daily_candle, crth, crtl)
    if not rejection:
        return None

    breakout = h4_breakout(h4)
    if not breakout:
        return None

    direction = None
    if rejection == "BEARISH" and breakout == "BEARISH_BREAKOUT":
        direction = "BEARISH"
    elif rejection == "BULLISH" and breakout == "BULLISH_BREAKOUT":
        direction = "BULLISH"
    else:
        return None

    trigger = model_one(m15, direction, crth, crtl)
    if not trigger:
        return None

    ob = order_block(m15, direction)
    if not ob:
        return None

    price = float(m15.iloc[-1].close)
    if not price_in_ob(price, ob):
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
        ob_low=ob["low"],
        ob_high=ob["high"],
        price=price,
    )
