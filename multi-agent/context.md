# Multi-Agent Crypto Trading Advisor — Context & Architecture

## Overview

A two-agent pipeline built with **LangGraph** that:
1. Fetches live coin prices from Binance
2. Analyzes those prices using technical trading indicators and gives a trend recommendation (UP / DOWN / NEUTRAL)

---

## LLM Client Configuration

```python
from openai import OpenAI

client = OpenAI(
    api_key="***REMOVED_OPENAI_KEY***",
    base_url="http://localhost:20128/v1"
)
```

> All LLM calls route through the local proxy at `localhost:20128/v1`.

---

## Agent Definitions

### Agent 1 — Price Fetcher (`price_agent`)

| Property | Value |
|---|---|
| **Role** | Data collector |
| **Tool** | Binance public REST API (no auth required) |
| **Endpoint** | `GET https://api.binance.com/api/v3/ticker/24hr` |
| **Coins** | BTC, ETH (extensible to any symbol) |
| **Output** | Dict of `{ symbol: { price, change_pct, high, low, volume } }` |

**What it fetches per coin:**
- `lastPrice` — current price in USDT
- `priceChangePercent` — 24h % change
- `highPrice` / `lowPrice` — 24h range
- `volume` — 24h trading volume

---

### Agent 2 — Technical Analyst (`analyst_agent`)

| Property | Value |
|---|---|
| **Role** | Market analyst |
| **Input** | Price data dict from Agent 1 |
| **Output** | Trend verdict + reasoning per coin |

**Technical indicators computed:**

| Indicator | Description | Signal logic |
|---|---|---|
| **24h Price Change %** | Simple momentum | `> +2%` = bullish, `< -2%` = bearish |
| **Price vs 24h High/Low** | Range position | Near high = bullish pressure, near low = bearish |
| **Volume trend** | Participation | High volume confirms trend direction |
| **RSI (simulated)** | Overbought/Oversold | Uses 24h high/low/close approximation |
| **Support/Resistance** | Key levels | Compares current price to daily range midpoint |

The analyst agent sends a structured prompt to the LLM with all indicators and asks for a reasoned verdict.

---

## LangGraph State & Flow

### State Schema

```python
class TradingState(TypedDict):
    coins: list[str]              # e.g. ["BTCUSDT", "ETHUSDT"]
    price_data: dict              # raw data from Agent 1
    analysis: dict                # verdict + reasoning from Agent 2
    error: str | None
```

### Graph Flow

```
START
  │
  ▼
[price_agent]          ← fetches Binance 24hr ticker for each coin
  │
  ▼
[analyst_agent]        ← runs technical analysis + calls LLM for verdict
  │
  ▼
[output_node]          ← formats and prints final report
  │
  ▼
END
```

### Edge Logic

- `price_agent → analyst_agent`: always (sequential pipeline)
- `analyst_agent → output_node`: always
- Error in `price_agent` → skip to `output_node` with error message

---

## File Structure

```
multi_agent_crypto/
├── context.md              ← this file
├── main.py                 ← entry point, builds and runs the graph
├── agents/
│   ├── __init__.py
│   ├── price_agent.py      ← Agent 1: Binance price fetcher
│   └── analyst_agent.py    ← Agent 2: technical analysis + LLM call
├── graph/
│   ├── __init__.py
│   └── builder.py          ← LangGraph StateGraph definition
├── tools/
│   ├── __init__.py
│   └── binance.py          ← Binance REST API wrapper
└── requirements.txt
```

---

## Requirements

```
langgraph>=0.2.0
langchain-core>=0.2.0
openai>=1.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## Key Implementation Notes

### `tools/binance.py`
- Use `requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT")`
- No API key needed for public market data
- Wrap in try/except and return structured dict

### `agents/price_agent.py`
- Node function signature: `def price_agent(state: TradingState) -> TradingState`
- Calls Binance tool for each coin in `state["coins"]`
- Writes result to `state["price_data"]`

### `agents/analyst_agent.py`
- Node function signature: `def analyst_agent(state: TradingState) -> TradingState`
- Computes indicators locally (no LLM needed for math)
- Builds a prompt summarizing all indicators
- Calls `client.chat.completions.create(...)` with the prompt
- Parses verdict (BULLISH / BEARISH / NEUTRAL) from LLM response
- Writes to `state["analysis"]`

### `graph/builder.py`
```python
from langgraph.graph import StateGraph, END
from agents.price_agent import price_agent
from agents.analyst_agent import analyst_agent

def build_graph():
    graph = StateGraph(TradingState)
    graph.add_node("price_agent", price_agent)
    graph.add_node("analyst_agent", analyst_agent)
    graph.add_node("output_node", output_node)

    graph.set_entry_point("price_agent")
    graph.add_edge("price_agent", "analyst_agent")
    graph.add_edge("analyst_agent", "output_node")
    graph.add_edge("output_node", END)

    return graph.compile()
```

### `main.py`
```python
from graph.builder import build_graph

app = build_graph()
result = app.invoke({
    "coins": ["BTCUSDT", "ETHUSDT"],
    "price_data": {},
    "analysis": {},
    "error": None
})
print(result["analysis"])
```

---

## Sample Output

```
========== CRYPTO TREND REPORT ==========

🪙 BTC/USDT
  Price       : $67,450.00
  24h Change  : +3.21%
  24h Range   : $64,800 – $68,100
  Volume      : 28,400 BTC
  Verdict     : 🟢 BULLISH
  Reasoning   : Price is near daily high with strong volume. Momentum
                is positive. RSI approximation suggests moderate buying
                pressure without being overbought.

🪙 ETH/USDT
  Price       : $3,510.00
  24h Change  : -1.05%
  24h Range   : $3,420 – $3,600
  Volume      : 142,000 ETH
  Verdict     : 🟡 NEUTRAL
  Reasoning   : Price sits at midpoint of daily range. Volume is average.
                No clear directional bias — wait for breakout above $3,600
                or breakdown below $3,420.

==========================================
```

---

## Extending the System

| Extension | How |
|---|---|
| Add more coins | Add symbols to `coins` list in `main.py` |
| Add more indicators | Fetch kline (candlestick) data from `/api/v3/klines` |
| Add real RSI/MACD | Use `pandas-ta` or `ta-lib` on kline data |
| Add a 3rd agent | Create `risk_agent` node in the graph for position sizing |
| Schedule runs | Wrap `app.invoke(...)` in a cron job or `asyncio` loop |