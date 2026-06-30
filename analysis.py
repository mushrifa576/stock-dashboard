import pandas as pd
import numpy as np

def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Add SMA and EMA columns."""
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()
    return df

def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Relative Strength Index — momentum oscillator (0-100)."""
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """MACD = EMA12 - EMA26, with signal line and histogram."""
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    return df

def add_bollinger_bands(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Upper/Lower bands = SMA ± 2 standard deviations."""
    df["BB_Mid"] = df["Close"].rolling(window=window).mean()
    std = df["Close"].rolling(window=window).std()
    df["BB_Upper"] = df["BB_Mid"] + 2 * std
    df["BB_Lower"] = df["BB_Mid"] - 2 * std
    return df

def add_volatility(df: pd.DataFrame) -> pd.DataFrame:
    """Annualized volatility from daily log returns."""
    df["Log_Return"] = np.log(df["Close"] / df["Close"].shift(1))
    df["Volatility"] = df["Log_Return"].rolling(window=20).std() * np.sqrt(252) * 100
    return df

def run_all(df: pd.DataFrame) -> pd.DataFrame:
    df = add_moving_averages(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_volatility(df)
    return df
