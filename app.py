import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
from data_fetcher import fetch_stock_data, fetch_stock_info, STOCK_LIST, INTERVALS
from analysis import run_all
from signals import detect_signals

# --- Page Config ---
st.set_page_config(page_title="📈 Stock Dashboard", layout="wide", page_icon="📈")

# Auto-refresh every 60 seconds
st_autorefresh(interval=60_000, key="live_refresh")

st.title("📈 Real-Time Stock Market Analytics Dashboard")
st.caption("Live data from Yahoo Finance · Auto-refreshes every 60 seconds")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ Settings")
    selected_label = st.selectbox("Select Stock", list(STOCK_LIST.keys()))
    ticker = STOCK_LIST[selected_label]

    interval_label = st.selectbox("Time Range", list(INTERVALS.keys()), index=2) # Default: 1 Month
    period, interval = INTERVALS[interval_label]

    show_sma = st.checkbox("Show SMA (20 & 50)", value=True)
    show_bb = st.checkbox("Show Bollinger Bands", value=True)
    show_volume = st.checkbox("Show Volume", value=True)

    st.divider()
    st.markdown("🔄 **Auto-refresh:** Every 60s")
    if st.button("🔃 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

# --- Fetch Data ---
with st.spinner(f"Fetching live data for {ticker}..."):
    df = fetch_stock_data(ticker, period, interval)

# ✅ Guard: Stop early if no data returned
if df is None or df.empty or len(df) < 2:
    st.warning(
        "⚠️ No data returned from Yahoo Finance. "
        "This can happen outside market hours or on weekends. "
        "Try switching to **'1 Month'** or **'3 Months'** in the Time Range."
    )
    st.stop()

# --- Process Indicators & Signals ---
df = run_all(df)
info = fetch_stock_info(ticker)
signals = detect_signals(df)

# --- Price Metrics ---
latest_price = df["Close"].iloc[-1]
prev_price = df["Close"].iloc[-2]
change = latest_price - prev_price
pct_change = (change / prev_price) * 100 if prev_price != 0 else 0

volatility = df["Volatility"].iloc[-1] if "Volatility" in df.columns else float("nan")
rsi_val = df["RSI"].iloc[-1] if "RSI" in df.columns else float("nan")

# --- Top KPIs ---
st.subheader(f"{info.get('name', ticker)} — {info.get('sector', '')}")

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("💰 Current Price",
          f"{latest_price:.2f}",
          f"{change:+.2f} ({pct_change:+.2f}%)")
k2.metric("📊 RSI",
          f"{rsi_val:.1f}" if not __import__('math').isnan(rsi_val) else "N/A")
k3.metric("📉 Volatility",
          f"{volatility:.1f}%" if not __import__('math').isnan(volatility) else "N/A")
k4.metric("🔝 52W High", str(info.get("52w_high", "N/A")))
k5.metric("🔻 52W Low", str(info.get("52w_low", "N/A")))
k6.metric("📈 P/E Ratio", str(info.get("pe_ratio", "N/A")))

st.divider()

# --- Main Chart ---
rows = 3 if show_volume else 2
row_heights = [0.6, 0.2, 0.2] if show_volume else [0.7, 0.3]
subplot_titles = (["Price & Indicators", "RSI", "Volume"]
                  if show_volume else ["Price & Indicators", "RSI"])

fig = make_subplots(
    rows=rows, cols=1,
    shared_xaxes=True,
    row_heights=row_heights,
    subplot_titles=subplot_titles,
    vertical_spacing=0.05
)

# Candlestick
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"],
    name="OHLC"
), row=1, col=1)

# Moving Averages
if show_sma and "SMA_20" in df.columns:
    fig.add_trace(go.Scatter(
        x=df.index, y=df["SMA_20"],
        name="SMA 20", line=dict(color="orange", width=1.5)
    ), row=1, col=1)
if show_sma and "SMA_50" in df.columns:
    fig.add_trace(go.Scatter(
        x=df.index, y=df["SMA_50"],
        name="SMA 50", line=dict(color="blue", width=1.5)
    ), row=1, col=1)

# Bollinger Bands
if show_bb and "BB_Upper" in df.columns:
    fig.add_trace(go.Scatter(
        x=df.index, y=df["BB_Upper"],
        name="BB Upper", line=dict(color="gray", dash="dash", width=1)
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["BB_Lower"],
        name="BB Lower",
        line=dict(color="gray", dash="dash", width=1),
        fill="tonexty", fillcolor="rgba(128,128,128,0.1)"
    ), row=1, col=1)

# RSI
if "RSI" in df.columns:
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"],
        name="RSI", line=dict(color="purple", width=1.5)
    ), row=2, col=1)
    fig.add_hline(y=70, line_color="red", line_dash="dash", row=2, col=1)
    fig.add_hline(y=30, line_color="green", line_dash="dash", row=2, col=1)

# Volume
if show_volume and "Volume" in df.columns:
    colors = [
        "green" if c >= o else "red"
        for c, o in zip(df["Close"], df["Open"])
    ]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        name="Volume", marker_color=colors
    ), row=3, col=1)

fig.update_layout(
    height=650,
    showlegend=True,
    xaxis_rangeslider_visible=False,
    template="plotly_dark"
)
st.plotly_chart(fig, use_container_width=True)

# --- Signals Panel ---
st.divider()
st.subheader("🚦 Trading Signals")

overall = signals.pop("OVERALL", "🟡 HOLD / NEUTRAL")
st.markdown(f"### Overall Consensus: {overall}")

if signals:
    cols = st.columns(len(signals))
    for col, (indicator, value) in zip(cols, signals.items()):
        with col:
            if isinstance(value, tuple):
                signal_label, reason = value
                st.markdown(f"**{indicator}**")
                st.markdown(signal_label)
                st.caption(reason)
            else:
                st.markdown(f"**{indicator}**")
                st.markdown(str(value))

# --- MACD Chart ---
if "MACD" in df.columns and df["MACD"].notna().any():
    st.divider()
    st.subheader("📉 MACD Indicator")
    macd_fig = go.Figure()
    macd_fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD"],
        name="MACD", line=dict(color="blue")
    ))
    macd_fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD_Signal"],
        name="Signal", line=dict(color="orange")
    ))
    macd_fig.add_trace(go.Bar(
        x=df.index, y=df["MACD_Hist"],
        name="Histogram",
        marker_color=["green" if v >= 0 else "red" for v in df["MACD_Hist"].fillna(0)]
    ))
    macd_fig.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(macd_fig, use_container_width=True)

# --- Raw Data ---
with st.expander("📋 View Raw Data"):
    display_cols = [c for c in
                    ["Open", "High", "Low", "Close", "Volume",
                     "SMA_20", "SMA_50", "RSI", "MACD", "Volatility"]
                    if c in df.columns]
    st.dataframe(df[display_cols].tail(50), use_container_width=True)
    csv = df.to_csv()
    st.download_button(
        "⬇️ Download CSV", csv,
        file_name=f"{ticker}_data.csv",
        mime="text/csv"
    )



