import argparse
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from graph.builder import build_graph
from tools.binance import normalize_symbol


def _default_coins() -> List[str]:
    raw = os.getenv("DEFAULT_COINS", "BTCUSDT,ETHUSDT")
    return [normalize_symbol(symbol) for symbol in raw.split(",") if symbol.strip()]


def _default_history_days() -> int:
    return int(os.getenv("HISTORY_DAYS", "180"))


def _default_forecast_days() -> int:
    return int(os.getenv("FORECAST_DAYS", "180"))


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _format_symbol(symbol: str) -> str:
    return symbol[:-4] + "/USDT" if symbol.endswith("USDT") else symbol


def format_report(result: Dict[str, Any]) -> str:
    lines = ["========== CRYPTO TREND REPORT ==========", ""]
    error = result.get("error")
    if error:
        lines.extend(["Notes:", f"  {error}", ""])

    analysis = result.get("analysis", {})
    if not analysis:
        lines.append("No analysis available.")
        lines.append("==========================================")
        return "\n".join(lines)

    for symbol, item in analysis.items():
        indicators = item["indicators"]
        levels = indicators.get("price_levels", {})
        forecast = indicators.get("forecast_levels", {})
        forecast_label = f"{forecast.get('horizon_days', indicators.get('forecast_days', 180))}d Forecast"
        lines.extend(
            [
                _format_symbol(symbol),
                f"  Price       : {_money(indicators['price'])}",
                f"  24h Change  : {indicators['change_pct']:+.2f}%",
                f"  Period      : {indicators['history_days']} days ({indicators['candle_count']} {indicators['interval']} candles)",
                f"  Period Chg  : {indicators['period_change_pct']:+.2f}%",
                f"  Range       : {_money(indicators['low'])} - {_money(indicators['high'])}",
                f"  RSI         : {indicators['rsi']:.2f}",
                f"  MA Trend    : {indicators['trend_signal']}",
                f"  News        : {indicators.get('news_sentiment', 'neutral')} ({indicators.get('news_article_count', 0)} CoinDesk articles)",
                f"  Likely Range: {_money(levels.get('near_term_low', indicators['price']))} - {_money(levels.get('near_term_high', indicators['price']))}",
                f"  Down Levels : {_money(levels.get('bearish_target_1', indicators['support']))}, {_money(levels.get('bearish_target_2', indicators['support']))}",
                f"  Up Levels   : {_money(levels.get('bullish_target_1', indicators['resistance']))}, {_money(levels.get('bullish_target_2', indicators['resistance']))}",
                f"  {forecast_label:<12}: {_money(forecast.get('expected_low', indicators['price']))} - {_money(forecast.get('expected_high', indicators['price']))}",
                f"  Forecast Base: {_money(forecast.get('base_case', indicators['price']))} ({forecast.get('base_return_pct', 0.0):+.2f}%)",
                f"  Bear/Bull   : {_money(forecast.get('bearish_case', indicators['price']))} / {_money(forecast.get('bullish_case', indicators['price']))}",
                f"  Volume      : {indicators['volume']:,.4f}",
                f"  Verdict     : {item['verdict']}",
                f"  Current Trend: {item.get('trend', 'SIDEWAYS')}",
                f"  Reasoning   : {item['reasoning']}",
            ]
        )
        for headline in indicators.get("news_headlines", [])[:3]:
            lines.append(f"  Headline    : {headline.get('title')}")
            if headline.get("link"):
                lines.append(f"                {headline.get('link')}")
        lines.append("")

    lines.append("==========================================")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the LangGraph crypto trading advisor.")
    parser.add_argument(
        "coins",
        nargs="*",
        help="Coin symbols, for example BTCUSDT ETHUSDT or BTC ETH.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=_default_history_days(),
        help="Historical lookback in days. Use 180 for about 6 months or 365 for about 1 year.",
    )
    parser.add_argument(
        "--interval",
        default=os.getenv("HISTORY_INTERVAL", "1d"),
        help="Binance kline interval, for example 1d, 12h, 4h, or 1w.",
    )
    parser.add_argument(
        "--forecast-days",
        type=int,
        default=_default_forecast_days(),
        help="Forward projection horizon in days. Default 180, about 6 months.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    coins = [normalize_symbol(symbol) for symbol in args.coins] if args.coins else _default_coins()

    app = build_graph()
    result = app.invoke(
        {
            "coins": coins,
            "history_days": args.days,
            "forecast_days": args.forecast_days,
            "interval": args.interval,
            "price_data": {},
            "news_data": {},
            "analysis": {},
            "error": None,
        }
    )
    print(format_report(result))


if __name__ == "__main__":
    main()
