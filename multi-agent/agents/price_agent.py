from copy import deepcopy

from state import TradingState
from tools.binance import BinanceAPIError, fetch_24hr_ticker, fetch_klines


def price_agent(state: TradingState) -> TradingState:
    next_state = deepcopy(state)
    price_data = {}
    errors = []
    history_days = int(next_state.get("history_days", 180))
    forecast_days = int(next_state.get("forecast_days", 180))
    interval = next_state.get("interval", "1d")

    for symbol in next_state.get("coins", []):
        try:
            ticker = fetch_24hr_ticker(symbol)
            candles = fetch_klines(ticker["symbol"], interval=interval, days=history_days)
            price_data[ticker["symbol"]] = {
                "ticker": ticker,
                "candles": candles,
                "history_days": history_days,
                "forecast_days": forecast_days,
                "interval": interval,
            }
        except BinanceAPIError as exc:
            errors.append(str(exc))

    next_state["price_data"] = price_data
    if errors:
        next_state["error"] = "; ".join(errors)

    return next_state
