import requests
import json
import pandas as pd
import numpy as np
import websocket
import sys
from datetime import datetime

# =========================
# CONFIG
# =========================
SYMBOL = "ethusdt"
INTERVAL = "1d"
BINANCE_WSS = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_{INTERVAL}"


# =========================
# INDICATORS
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal


def update_indicators(df):
    df["MA20"] = df["close"].rolling(20).mean()
    df["MA50"] = df["close"].rolling(50).mean()
    df["RSI"] = rsi(df["close"])
    df["MACD"], df["Signal"] = macd(df["close"])
    return df


# =========================
# INITIAL DATA LOAD & PRINT
# =========================
def get_historical_and_display():
    print(f"[*] Loading historical data for {SYMBOL.upper()}...")
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": SYMBOL.upper(), "interval": INTERVAL, "limit": 500}

    raw = requests.get(url, params=params).json()
    df = pd.DataFrame(raw, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tb_base", "tb_quote", "ignore"
    ])

    df["time"] = pd.to_datetime(df["time"], unit='ms')
    df.set_index("time", inplace=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df = update_indicators(df)

    # Print the Header
    header = f"{'Date':<20} | {'Close':<10} | {'MA20':<10} | {'MA50':<10} | {'RSI':<8} | {'MACD':<10} | {'Signal':<10}"
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))

    # Print All Historical Rows
    for timestamp, row in df.iterrows():
        ma20 = f"{row['MA20']:>10.2f}" if not np.isnan(row['MA20']) else f"{'N/A':>10}"
        ma50 = f"{row['MA50']:>10.2f}" if not np.isnan(row['MA50']) else f"{'N/A':>10}"
        rsi_v = f"{row['RSI']:>8.2f}" if not np.isnan(row['RSI']) else f"{'N/A':>8}"

        print(
            f"{str(timestamp):<20} | {row['close']:>10.2f} | {ma20} | {ma50} | {rsi_v} | {row['MACD']:>10.4f} | {row['Signal']:>10.4f}")

    return df


# Global state
main_df = get_historical_and_display()


# =========================
# WEBSOCKET HANDLERS
# =========================
def on_message(ws, message):
    global main_df
    data = json.loads(message)
    k = data['k']

    timestamp = pd.to_datetime(k['t'], unit='ms')
    close_price = float(k['c'])

    # Update the row for the current day
    main_df.loc[timestamp, "close"] = close_price
    main_df = update_indicators(main_df)

    last = main_df.iloc[-1]

    # Live Ticker at the bottom
    sys.stdout.write(
        f"\r>> LIVE UPDATE | {timestamp} | Price: {close_price:10.2f} | "
        f"RSI: {last['RSI']:6.2f} | MACD: {last['MACD']:8.4f} | Signal: {last['Signal']:8.4f}"
    )
    sys.stdout.flush()


def on_open(ws):
    print("-" * 105)
    print("[!] LIVE STREAM STARTED. The line below will update in real-time.")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    ws_app = websocket.WebSocketApp(
        BINANCE_WSS,
        on_open=on_open,
        on_message=on_message
    )
    ws_app.run_forever()