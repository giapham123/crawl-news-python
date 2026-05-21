import html
import os
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List

import requests

DEFAULT_COINDESK_RSS_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"

COIN_KEYWORDS = {
    "BTC": ["btc", "bitcoin"],
    "ETH": ["eth", "ether", "ethereum"],
    "BNB": ["bnb", "binance coin"],
    "SOL": ["sol", "solana"],
    "XRP": ["xrp", "ripple"],
    "ADA": ["ada", "cardano"],
    "DOGE": ["doge", "dogecoin"],
}

POSITIVE_WORDS = {
    "adoption",
    "approve",
    "approved",
    "bull",
    "bullish",
    "breakout",
    "buy",
    "climb",
    "gain",
    "gains",
    "growth",
    "high",
    "inflow",
    "inflows",
    "rally",
    "recover",
    "rise",
    "rises",
    "surge",
    "up",
}

NEGATIVE_WORDS = {
    "bear",
    "bearish",
    "ban",
    "crackdown",
    "crash",
    "decline",
    "drop",
    "drops",
    "exploit",
    "fall",
    "falls",
    "hack",
    "lawsuit",
    "liquidation",
    "outflow",
    "outflows",
    "plunge",
    "risk",
    "sell",
    "slump",
    "weak",
}


class CoinDeskAPIError(RuntimeError):
    pass


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _child_text(item: ET.Element, name: str) -> str:
    child = item.find(name)
    return _strip_html(child.text if child is not None and child.text else "")


def _article_from_item(item: ET.Element) -> Dict[str, Any]:
    published_raw = _child_text(item, "pubDate")
    published_iso = published_raw
    if published_raw:
        try:
            published_iso = parsedate_to_datetime(published_raw).isoformat()
        except (TypeError, ValueError):
            published_iso = published_raw

    return {
        "title": _child_text(item, "title"),
        "link": _child_text(item, "link"),
        "published": published_iso,
        "summary": _child_text(item, "description"),
    }


def fetch_coindesk_articles(limit: int = 25, timeout: float = 10.0) -> List[Dict[str, Any]]:
    url = os.getenv("COINDESK_RSS_URL", DEFAULT_COINDESK_RSS_URL)
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CoinDeskAPIError(f"Failed to fetch CoinDesk RSS feed: {exc}") from exc

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise CoinDeskAPIError("CoinDesk RSS feed returned invalid XML") from exc

    articles = [_article_from_item(item) for item in root.findall("./channel/item")]
    return [article for article in articles if article["title"]][:limit]


def _symbol_base(symbol: str) -> str:
    normalized = symbol.upper().replace("/", "")
    return normalized[:-4] if normalized.endswith("USDT") else normalized


def _sentiment_score(text: str) -> int:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return len(words & POSITIVE_WORDS) - len(words & NEGATIVE_WORDS)


def summarize_news_for_symbols(
    symbols: List[str],
    articles: List[Dict[str, Any]],
    per_symbol_limit: int = 5,
) -> Dict[str, Dict[str, Any]]:
    news_by_symbol = {}
    for symbol in symbols:
        base = _symbol_base(symbol)
        keywords = COIN_KEYWORDS.get(base, [base.lower()])
        matches = []
        score = 0

        for article in articles:
            haystack = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            if not any(keyword in haystack for keyword in keywords):
                continue
            article_score = _sentiment_score(haystack)
            score += article_score
            enriched = dict(article)
            enriched["sentiment_score"] = article_score
            matches.append(enriched)
            if len(matches) >= per_symbol_limit:
                break

        sentiment = "neutral"
        if score > 1:
            sentiment = "bullish"
        elif score < -1:
            sentiment = "bearish"

        news_by_symbol[symbol] = {
            "source": "CoinDesk",
            "sentiment": sentiment,
            "sentiment_score": score,
            "articles": matches,
        }

    return news_by_symbol
