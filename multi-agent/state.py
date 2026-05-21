from typing import Any, Dict, List, Optional, TypedDict


class TradingState(TypedDict):
    coins: List[str]
    history_days: int
    forecast_days: int
    interval: str
    price_data: Dict[str, Dict[str, Any]]
    news_data: Dict[str, Dict[str, Any]]
    analysis: Dict[str, Dict[str, Any]]
    error: Optional[str]
