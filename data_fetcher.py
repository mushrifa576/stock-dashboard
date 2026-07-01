import yfinance as yf
import pandas as pd
import streamlit as st

# Popular stocks with friendly labels
STOCK_LIST = {
    "Apple (AAPL)": "AAPL",
    "Google (GOOGL)": "GOOGL",
    "Microsoft (MSFT)": "MSFT",
    "Tesla (TSLA)": "TSLA",
    "Amazon (AMZN)": "AMZN",
    "NVIDIA (NVDA)": "NVDA",
    "Meta (META)": "META",
    "Infosys (INFY)": "INFY",
    "TCS (TCS.NS)": "TCS.NS",
    "Reliance (RELIANCE.NS)": "RELIANCE.NS",
}

INTERVALS = {
    "1 Day (5-min candles)": ("1d", "5m"),
    "5 Days (15-min candles)": ("5d", "15m"),
    "1 Month (1-day candles)": ("1mo", "1d"),
    "3 Months (1-day candles)": ("3mo", "1d"),
    "1 Year (1-week candles)": ("1y", "1wk"),
}

@st.cache_data(ttl=60)
def fetch_stock_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetch OHLCV data from Yahoo Finance with error handling."""
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)

        if df is None or df.empty:
            return pd.DataFrame()

        # Flatten MultiIndex columns if present
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

        df.dropna(how="all", inplace=True)
        df = df[df["Close"].notna()] # Keep only rows with valid close price

        return df

    except Exception as e:
        st.error(f"❌ Failed to fetch data for {ticker}: {e}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()

def fetch_stock_info(ticker: str) -> dict:
    """Fetch company metadata with error handling."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
            "currency": info.get("currency", "USD"),
        }
    except Exception:
        return {
            "name": ticker,
            "sector": "N/A",
            "market_cap": 0,
            "pe_ratio": "N/A",
            "52w_high": "N/A",
            "52w_low": "N/A",
            "currency": "USD",
        }

