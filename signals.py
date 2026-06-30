import pandas as pd

def detect_signals(df: pd.DataFrame) -> dict:
    """Generate BUY / SELL / HOLD signals from multiple indicators."""
    
    signals = {}

    # ✅ Guard: return safe defaults if not enough data
    if df is None or len(df) < 2:
        return {
            "RSI": ("🟡 HOLD", "Not enough data to calculate RSI"),
            "MACD": ("🟡 HOLD", "Not enough data to calculate MACD"),
            "MA": ("🟡 HOLD", "Not enough data to calculate Moving Averages"),
            "Bollinger": ("🟡 HOLD", "Not enough data to calculate Bollinger Bands"),
            "OVERALL": "🟡 HOLD / NEUTRAL"
        }

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # --- RSI Signal ---
    rsi = latest.get("RSI", 50)
    if pd.isna(rsi):
        signals["RSI"] = ("🟡 HOLD", "RSI not yet calculated (need more data)")
    elif rsi < 30:
        signals["RSI"] = ("🟢 BUY", f"Oversold (RSI = {rsi:.1f} < 30) — potential reversal upward")
    elif rsi > 70:
        signals["RSI"] = ("🔴 SELL", f"Overbought (RSI = {rsi:.1f} > 70) — potential reversal downward")
    else:
        signals["RSI"] = ("🟡 HOLD", f"Neutral RSI at {rsi:.1f}")

    # --- MACD Signal ---
    macd_now = latest.get("MACD", None)
    macd_sig_now = latest.get("MACD_Signal", None)
    macd_prev = prev.get("MACD", None)
    macd_sig_prev = prev.get("MACD_Signal", None)

    if any(pd.isna(v) for v in [macd_now, macd_sig_now, macd_prev, macd_sig_prev] if v is not None):
        signals["MACD"] = ("🟡 HOLD", "MACD not yet calculated (need more data)")
    elif macd_now > macd_sig_now and macd_prev <= macd_sig_prev:
        signals["MACD"] = ("🟢 BUY", "MACD crossed above signal line — bullish momentum")
    elif macd_now < macd_sig_now and macd_prev >= macd_sig_prev:
        signals["MACD"] = ("🔴 SELL", "MACD crossed below signal line — bearish momentum")
    else:
        signals["MACD"] = ("🟡 HOLD", "No MACD crossover detected")

    # --- Moving Average Signal ---
    sma20 = latest.get("SMA_20", None)
    sma50 = latest.get("SMA_50", None)
    close = latest.get("Close", None)

    if close is None or pd.isna(close):
        signals["MA"] = ("🟡 HOLD", "Price data unavailable")
    elif sma20 is None or sma50 is None or pd.isna(sma20) or pd.isna(sma50):
        signals["MA"] = ("🟡 HOLD", "Moving averages not yet calculated (need more data)")
    elif close > sma20 > sma50:
        signals["MA"] = ("🟢 BUY", "Price above SMA20 > SMA50 — strong uptrend")
    elif close < sma20 < sma50:
        signals["MA"] = ("🔴 SELL", "Price below SMA20 < SMA50 — strong downtrend")
    else:
        signals["MA"] = ("🟡 HOLD", "Mixed moving average signals")

    # --- Bollinger Band Signal ---
    bb_lower = latest.get("BB_Lower", None)
    bb_upper = latest.get("BB_Upper", None)

    if bb_lower is None or bb_upper is None or pd.isna(bb_lower) or pd.isna(bb_upper):
        signals["Bollinger"] = ("🟡 HOLD", "Bollinger Bands not yet calculated (need more data)")
    elif close is not None and not pd.isna(close):
        if close <= bb_lower:
            signals["Bollinger"] = ("🟢 BUY", "Price at lower Bollinger Band — possible bounce")
        elif close >= bb_upper:
            signals["Bollinger"] = ("🔴 SELL", "Price at upper Bollinger Band — possible pullback")
        else:
            signals["Bollinger"] = ("🟡 HOLD", "Price within Bollinger Bands — no extreme signal")
    else:
        signals["Bollinger"] = ("🟡 HOLD", "Price data unavailable")

    # --- Overall Consensus ---
    buys = sum(1 for s in signals.values() if isinstance(s, tuple) and "BUY" in s[0])
    sells = sum(1 for s in signals.values() if isinstance(s, tuple) and "SELL" in s[0])

    if buys >= 3:
        signals["OVERALL"] = "🟢 STRONG BUY"
    elif sells >= 3:
        signals["OVERALL"] = "🔴 STRONG SELL"
    elif buys > sells:
        signals["OVERALL"] = "🟢 MILD BUY"
    elif sells > buys:
        signals["OVERALL"] = "🔴 MILD SELL"
    else:
        signals["OVERALL"] = "🟡 HOLD / NEUTRAL"

    return signals

