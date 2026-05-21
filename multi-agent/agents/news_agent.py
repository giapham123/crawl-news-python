from copy import deepcopy

from state import TradingState
from tools.coindesk import CoinDeskAPIError, fetch_coindesk_articles, summarize_news_for_symbols


def news_agent(state: TradingState) -> TradingState:
    next_state = deepcopy(state)
    symbols = list(next_state.get("price_data", {}).keys()) or next_state.get("coins", [])

    try:
        articles = fetch_coindesk_articles()
        next_state["news_data"] = summarize_news_for_symbols(symbols, articles)
    except CoinDeskAPIError as exc:
        next_state["news_data"] = {}
        prior_error = next_state.get("error")
        news_error = str(exc)
        next_state["error"] = f"{prior_error}; {news_error}" if prior_error else news_error

    return next_state
