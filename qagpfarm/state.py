from typing import Dict, List, Optional, TypedDict


class GPFarmState(TypedDict):
    query: str
    routed_query: str
    intent: str
    answer: str
    history: List[Dict[str, str]]
    error: Optional[str]
