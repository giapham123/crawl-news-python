import json
import os
import re
from copy import deepcopy
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from state import TradingState


load_dotenv()

VERDICTS = {"BULLISH", "BEARISH", "NEUTRAL"}
TREND_BY_VERDICT = {
    "BULLISH": "UP",
    "BEARISH": "DOWN",
    "NEUTRAL": "SIDEWAYS",
}


def _client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "local-proxy-key"),
        base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:20128/v1"),
    )


def _sma(values: List[float], window: int) -> Optional[float]:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def _rsi(values: List[float], window: int = 14) -> Optional[float]:
    if len(values) <= window:
        return None

    gains = []
    losses = []
    for previous, current in zip(values[-window - 1 : -1], values[-window:]):
        change = current - previous
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))

    average_gain = sum(gains) / window
    average_loss = sum(losses) / window
    if average_loss == 0:
        return 100.0
    relative_strength = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def _average_true_range(candles: List[Dict[str, Any]], window: int = 14) -> Optional[float]:
    if len(candles) < 2:
        return None

    true_ranges = []
    recent = candles[-window:]
    previous_close = float(candles[-len(recent) - 1]["close"]) if len(candles) > len(recent) else None
    for candle in recent:
        high = float(candle["high"])
        low = float(candle["low"])
        if previous_close is None:
            true_range = high - low
        else:
            true_range = max(high - low, abs(high - previous_close), abs(low - previous_close))
        true_ranges.append(true_range)
        previous_close = float(candle["close"])

    return sum(true_ranges) / len(true_ranges) if true_ranges else None


def _nearest_levels(price: float, levels: List[float], below: bool) -> List[float]:
    unique_levels = sorted({round(level, 8) for level in levels if level > 0})
    filtered = [level for level in unique_levels if level < price] if below else [level for level in unique_levels if level > price]
    ordered = sorted(filtered, key=lambda level: abs(price - level))
    return ordered[:3]


def _price_levels(
    price: float,
    low: float,
    high: float,
    midpoint: float,
    candles: List[Dict[str, Any]],
    sma_20: Optional[float],
    sma_50: Optional[float],
    sma_200: Optional[float],
) -> Dict[str, Any]:
    atr = _average_true_range(candles) or max((high - low) * 0.05, price * 0.02)
    recent = candles[-30:] if candles else []
    recent_low = min(float(candle["low"]) for candle in recent) if recent else low
    recent_high = max(float(candle["high"]) for candle in recent) if recent else high
    candidate_levels = [low, high, midpoint, recent_low, recent_high]
    candidate_levels.extend([level for level in [sma_20, sma_50, sma_200] if level])

    support_levels = _nearest_levels(price, candidate_levels, below=True)
    resistance_levels = _nearest_levels(price, candidate_levels, below=False)
    if not support_levels:
        support_levels = [max(price - atr, 0.0), max(price - (2 * atr), 0.0)]
    if not resistance_levels:
        resistance_levels = [price + atr, price + (2 * atr)]

    return {
        "atr": atr,
        "near_term_low": max(price - atr, 0.0),
        "near_term_high": price + atr,
        "bearish_target_1": support_levels[0],
        "bearish_target_2": support_levels[1] if len(support_levels) > 1 else max(support_levels[0] - atr, 0.0),
        "bullish_target_1": resistance_levels[0],
        "bullish_target_2": resistance_levels[1] if len(resistance_levels) > 1 else resistance_levels[0] + atr,
        "support_levels": support_levels,
        "resistance_levels": resistance_levels,
    }


def _daily_returns(values: List[float]) -> List[float]:
    returns = []
    for previous, current in zip(values[:-1], values[1:]):
        if previous:
            returns.append((current - previous) / previous)
    return returns


def _standard_deviation(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return variance ** 0.5


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _forecast_levels(
    price: float,
    closes: List[float],
    period_change_pct: float,
    history_days: int,
    forecast_days: int,
    trend_signal: str,
    news_sentiment: str,
) -> Dict[str, Any]:
    usable_history_days = max(history_days, 1)
    returns = _daily_returns(closes[-180:] if len(closes) > 180 else closes)
    daily_volatility = _standard_deviation(returns) if returns else 0.02
    horizon_volatility = daily_volatility * (max(forecast_days, 1) ** 0.5)

    historical_return = period_change_pct / 100.0
    momentum_projection = historical_return * (forecast_days / usable_history_days)
    momentum_projection = _clamp(momentum_projection, -0.80, 1.50)

    signal_adjustment = 0.0
    if trend_signal == "bullish":
        signal_adjustment += 0.08
    elif trend_signal == "bearish":
        signal_adjustment -= 0.08

    if news_sentiment == "bullish":
        signal_adjustment += 0.05
    elif news_sentiment == "bearish":
        signal_adjustment -= 0.05

    base_return = _clamp(momentum_projection + signal_adjustment, -0.85, 1.75)
    bearish_return = _clamp(base_return - max(horizon_volatility * 0.65, 0.08), -0.90, 2.00)
    bullish_return = _clamp(base_return + max(horizon_volatility * 0.65, 0.08), -0.90, 2.50)
    expected_low_return = _clamp(base_return - max(horizon_volatility * 0.35, 0.05), -0.90, 2.00)
    expected_high_return = _clamp(base_return + max(horizon_volatility * 0.35, 0.05), -0.90, 2.25)

    return {
        "horizon_days": forecast_days,
        "base_case": price * (1.0 + base_return),
        "bearish_case": price * (1.0 + bearish_return),
        "bullish_case": price * (1.0 + bullish_return),
        "expected_low": price * (1.0 + expected_low_return),
        "expected_high": price * (1.0 + expected_high_return),
        "base_return_pct": base_return * 100.0,
        "bearish_return_pct": bearish_return * 100.0,
        "bullish_return_pct": bullish_return * 100.0,
        "historical_momentum_projection_pct": momentum_projection * 100.0,
        "volatility_estimate_pct": horizon_volatility * 100.0,
    }


def compute_indicators(price_record: Dict[str, Any]) -> Dict[str, Any]:
    ticker = price_record.get("ticker", price_record)
    candles = price_record.get("candles", [])
    price = float(ticker["price"])
    closes = [float(candle["close"]) for candle in candles]
    highs = [float(candle["high"]) for candle in candles]
    lows = [float(candle["low"]) for candle in candles]
    volumes = [float(candle["volume"]) for candle in candles]

    high = max(highs) if highs else float(ticker["high"])
    low = min(lows) if lows else float(ticker["low"])
    open_price = float(candles[0]["open"]) if candles else price
    change_pct = float(ticker["change_pct"])
    period_change_pct = ((price - open_price) / open_price * 100) if open_price else 0.0
    period_range = max(high - low, 0.0)
    midpoint = (high + low) / 2 if high and low else price
    range_position = ((price - low) / period_range) if period_range else 0.5
    range_position = max(0.0, min(1.0, range_position))
    sma_20 = _sma(closes, 20)
    sma_50 = _sma(closes, 50)
    sma_200 = _sma(closes, 200)
    rsi_value = _rsi(closes) if closes else None

    if rsi_value is None:
        rsi_value = max(0.0, min(100.0, 100.0 * range_position))

    recent_volume = sum(volumes[-20:]) / min(len(volumes), 20) if volumes else float(ticker["volume"])
    prior_slice = volumes[-40:-20]
    prior_volume = sum(prior_slice) / len(prior_slice) if prior_slice else recent_volume
    volume_trend_pct = ((recent_volume - prior_volume) / prior_volume * 100) if prior_volume else 0.0

    momentum = "bullish" if period_change_pct > 5 else "bearish" if period_change_pct < -5 else "neutral"
    range_signal = "near_high" if range_position >= 0.75 else "near_low" if range_position <= 0.25 else "mid_range"
    rsi_signal = "overbought" if rsi_value >= 70 else "oversold" if rsi_value <= 30 else "balanced"
    trend_signal = "neutral"
    if sma_50 and sma_200:
        trend_signal = "bullish" if sma_50 > sma_200 else "bearish"
    elif sma_20 and sma_50:
        trend_signal = "bullish" if sma_20 > sma_50 else "bearish"
    support_distance_pct = ((price - low) / price * 100) if price else 0.0
    resistance_distance_pct = ((high - price) / price * 100) if price else 0.0
    history_days = int(price_record.get("history_days", 1))
    forecast_days = int(price_record.get("forecast_days", 180))
    levels = _price_levels(price, low, high, midpoint, candles, sma_20, sma_50, sma_200)
    forecast_levels = _forecast_levels(
        price,
        closes,
        period_change_pct,
        history_days,
        forecast_days,
        trend_signal,
        price_record.get("news_sentiment", "neutral"),
    )

    return {
        "price": price,
        "change_pct": change_pct,
        "high": high,
        "low": low,
        "volume": float(ticker["volume"]),
        "quote_volume": float(ticker.get("quote_volume", 0.0)),
        "history_days": history_days,
        "forecast_days": forecast_days,
        "interval": price_record.get("interval", "1d"),
        "candle_count": len(candles),
        "period_change_pct": period_change_pct,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "midpoint": midpoint,
        "range_position_pct": range_position * 100,
        "rsi": rsi_value,
        "momentum_signal": momentum,
        "range_signal": range_signal,
        "rsi_signal": rsi_signal,
        "trend_signal": trend_signal,
        "recent_avg_volume": recent_volume,
        "prior_avg_volume": prior_volume,
        "volume_trend_pct": volume_trend_pct,
        "support": low,
        "resistance": high,
        "support_distance_pct": support_distance_pct,
        "resistance_distance_pct": resistance_distance_pct,
        "price_levels": levels,
        "forecast_levels": forecast_levels,
    }


def heuristic_verdict(indicators: Dict[str, Any]) -> str:
    score = 0
    if indicators["period_change_pct"] > 5:
        score += 1
    elif indicators["period_change_pct"] < -5:
        score -= 1

    if indicators["range_position_pct"] >= 75:
        score += 1
    elif indicators["range_position_pct"] <= 25:
        score -= 1

    if indicators["rsi"] >= 75:
        score -= 1
    elif indicators["rsi"] <= 25:
        score += 1

    if indicators["trend_signal"] == "bullish":
        score += 1
    elif indicators["trend_signal"] == "bearish":
        score -= 1

    news_sentiment = indicators.get("news_sentiment")
    if news_sentiment == "bullish":
        score += 1
    elif news_sentiment == "bearish":
        score -= 1

    if score >= 1:
        return "BULLISH"
    if score <= -1:
        return "BEARISH"
    return "NEUTRAL"


def current_trend(verdict: str) -> str:
    return TREND_BY_VERDICT.get(verdict, "SIDEWAYS")


def _fallback_reasoning(symbol: str, indicators: Dict[str, Any]) -> str:
    news_text = "CoinDesk news is neutral or unavailable"
    if indicators.get("news_headlines"):
        news_text = (
            f"CoinDesk news sentiment is {indicators['news_sentiment']} "
            f"from {indicators['news_article_count']} matched headline(s)"
        )
    return (
        f"{symbol} has {indicators['period_change_pct']:.2f}% momentum over "
        f"{indicators['history_days']} days using {indicators['candle_count']} "
        f"{indicators['interval']} candles. It trades at {indicators['range_position_pct']:.1f}% "
        f"of that range, RSI is {indicators['rsi']:.1f}, and moving-average trend is "
        f"{indicators['trend_signal']}. Support is near {indicators['support']:.2f}; "
        f"resistance is near {indicators['resistance']:.2f}. Likely near-term range is "
        f"{indicators['price_levels']['near_term_low']:.2f} to "
        f"{indicators['price_levels']['near_term_high']:.2f}. The {indicators['forecast_days']}-day "
        f"base forecast is around {indicators['forecast_levels']['base_case']:.2f}, with an expected "
        f"zone of {indicators['forecast_levels']['expected_low']:.2f} to "
        f"{indicators['forecast_levels']['expected_high']:.2f}. {news_text}."
    )


def _build_prompt(indicator_map: Dict[str, Dict[str, Any]]) -> str:
    return (
        "You are a concise crypto technical analyst. Review these Binance historical "
        "price indicators and return JSON only. Use verdict values BULLISH, BEARISH, or NEUTRAL. "
        "Include likely price levels and forward forecast levels in the reasoning using the "
        "provided price_levels and forecast_levels objects. "
        "Schema: {\"SYMBOL\": {\"verdict\": \"...\", \"reasoning\": \"...\"}}.\n\n"
        f"Indicators:\n{json.dumps(indicator_map, indent=2, sort_keys=True)}"
    )


def _parse_llm_json(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def _extract_verdict(value: Any) -> Optional[str]:
    text = value if isinstance(value, str) else json.dumps(value)
    match = re.search(r"\b(BULLISH|BEARISH|NEUTRAL)\b", text.upper())
    return match.group(1) if match else None


def analyst_agent(state: TradingState) -> TradingState:
    next_state = deepcopy(state)
    price_data = next_state.get("price_data", {})
    if not price_data:
        next_state["analysis"] = {}
        next_state["error"] = next_state.get("error") or "No price data available for analysis"
        return next_state

    news_data = next_state.get("news_data", {})
    indicators = {}
    for symbol, ticker in price_data.items():
        symbol_news = news_data.get(symbol, {})
        enriched_ticker = dict(ticker)
        enriched_ticker["news_sentiment"] = symbol_news.get("sentiment", "neutral")
        symbol_indicators = compute_indicators(enriched_ticker)
        articles = symbol_news.get("articles", [])
        symbol_indicators["news_source"] = symbol_news.get("source", "CoinDesk")
        symbol_indicators["news_sentiment"] = symbol_news.get("sentiment", "neutral")
        symbol_indicators["news_sentiment_score"] = symbol_news.get("sentiment_score", 0)
        symbol_indicators["news_article_count"] = len(articles)
        symbol_indicators["news_headlines"] = [
            {
                "title": article.get("title"),
                "published": article.get("published"),
                "link": article.get("link"),
                "sentiment_score": article.get("sentiment_score", 0),
            }
            for article in articles
        ]
        indicators[symbol] = symbol_indicators
    analysis = {
        symbol: {
            "verdict": heuristic_verdict(symbol_indicators),
            "trend": current_trend(heuristic_verdict(symbol_indicators)),
            "reasoning": _fallback_reasoning(symbol, symbol_indicators),
            "indicators": symbol_indicators,
            "source": "heuristic",
        }
        for symbol, symbol_indicators in indicators.items()
    }

    try:
        response = _client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "cx/gpt-5.3-codex-none"),
            messages=[
                {"role": "system", "content": "Return compact JSON only. Do not include markdown."},
                {"role": "user", "content": _build_prompt(indicators)},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        llm_payload = _parse_llm_json(content)
        for symbol, payload in llm_payload.items():
            normalized_symbol = symbol.upper().replace("/", "")
            if normalized_symbol not in analysis:
                continue
            verdict = _extract_verdict(payload)
            if verdict in VERDICTS:
                analysis[normalized_symbol]["verdict"] = verdict
                analysis[normalized_symbol]["trend"] = current_trend(verdict)
            if isinstance(payload, dict) and payload.get("reasoning"):
                analysis[normalized_symbol]["reasoning"] = str(payload["reasoning"])
            elif isinstance(payload, str):
                analysis[normalized_symbol]["reasoning"] = payload
            analysis[normalized_symbol]["source"] = "llm"
    except Exception as exc:
        prior_error = next_state.get("error")
        llm_error = f"LLM analysis failed, used heuristic fallback: {exc}"
        next_state["error"] = f"{prior_error}; {llm_error}" if prior_error else llm_error

    next_state["analysis"] = analysis
    return next_state
