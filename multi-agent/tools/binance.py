import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests


DEFAULT_BINANCE_BASE_URL = "https://api.binance.com"


class BinanceAPIError(RuntimeError):
    pass


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise BinanceAPIError(f"Unexpected numeric value from Binance: {value!r}") from exc


def normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper().replace("/", "")
    if not normalized:
        raise BinanceAPIError("Coin symbol cannot be empty")
    if normalized in {"BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE"}:
        normalized = f"{normalized}USDT"
    return normalized


def fetch_24hr_ticker(symbol: str, timeout: float = 10.0) -> Dict[str, Any]:
    normalized_symbol = normalize_symbol(symbol)
    base_url = os.getenv("BINANCE_BASE_URL", DEFAULT_BINANCE_BASE_URL).rstrip("/")
    url = f"{base_url}/api/v3/ticker/24hr"

    try:
        response = requests.get(url, params={"symbol": normalized_symbol}, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise BinanceAPIError(f"Failed to fetch Binance ticker for {normalized_symbol}: {exc}") from exc
    except ValueError as exc:
        raise BinanceAPIError(f"Binance returned invalid JSON for {normalized_symbol}") from exc

    if "code" in payload and "msg" in payload:
        raise BinanceAPIError(f"Binance error for {normalized_symbol}: {payload['msg']}")

    return {
        "symbol": normalized_symbol,
        "price": _as_float(payload.get("lastPrice")),
        "change_pct": _as_float(payload.get("priceChangePercent")),
        "high": _as_float(payload.get("highPrice")),
        "low": _as_float(payload.get("lowPrice")),
        "volume": _as_float(payload.get("volume")),
        "quote_volume": _as_float(payload.get("quoteVolume")),
        "raw": payload,
    }


def _parse_kline(row: List[Any]) -> Dict[str, Any]:
    return {
        "open_time": int(row[0]),
        "open_time_iso": datetime.utcfromtimestamp(int(row[0]) / 1000).isoformat() + "Z",
        "open": _as_float(row[1]),
        "high": _as_float(row[2]),
        "low": _as_float(row[3]),
        "close": _as_float(row[4]),
        "volume": _as_float(row[5]),
        "close_time": int(row[6]),
        "quote_volume": _as_float(row[7]),
        "trades": int(row[8]),
    }


def fetch_klines(
    symbol: str,
    interval: str = "1d",
    days: int = 180,
    timeout: float = 10.0,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    normalized_symbol = normalize_symbol(symbol)
    if days <= 0:
        raise BinanceAPIError("History days must be greater than zero")

    base_url = os.getenv("BINANCE_BASE_URL", DEFAULT_BINANCE_BASE_URL).rstrip("/")
    url = f"{base_url}/api/v3/klines"
    end_ms = int(time.time() * 1000)
    start_ms = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    rows = []

    try:
        while start_ms < end_ms:
            response = requests.get(
                url,
                params={
                    "symbol": normalized_symbol,
                    "interval": interval,
                    "startTime": start_ms,
                    "endTime": end_ms,
                    "limit": limit,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and "code" in payload and "msg" in payload:
                raise BinanceAPIError(f"Binance error for {normalized_symbol}: {payload['msg']}")
            if not payload:
                break
            rows.extend(payload)
            last_open_time = int(payload[-1][0])
            next_start = last_open_time + 1
            if next_start <= start_ms or len(payload) < limit:
                break
            start_ms = next_start
    except requests.RequestException as exc:
        raise BinanceAPIError(f"Failed to fetch Binance klines for {normalized_symbol}: {exc}") from exc
    except ValueError as exc:
        raise BinanceAPIError(f"Binance returned invalid kline JSON for {normalized_symbol}") from exc

    return [_parse_kline(row) for row in rows]
