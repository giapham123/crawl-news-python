from langgraph.graph import END, StateGraph

from qagpfarm.qa import GPFarmQA, INTENTS
from qagpfarm.state import GPFarmState


def _safe_intent(intent: str) -> str:
    return intent if intent in INTENTS else "product_info"


def build_graph(assistant: GPFarmQA):
    graph = StateGraph(GPFarmState)

    def orchestrator_agent(state: GPFarmState) -> GPFarmState:
        try:
            routed = assistant.classify(state["query"])
            return {
                **state,
                "intent": _safe_intent(routed.intent),
                "routed_query": routed.query,
                "error": None,
            }
        except Exception as exc:
            return {
                **state,
                "intent": "product_info",
                "routed_query": state["query"],
                "error": str(exc),
            }

    def product_info_agent(state: GPFarmState) -> GPFarmState:
        return {
            **state,
            "answer": assistant.answer_with_intent(
                "product_info",
                state.get("routed_query") or state["query"],
                history=state.get("history", []),
            ),
        }

    def price_stock_agent(state: GPFarmState) -> GPFarmState:
        return {
            **state,
            "answer": assistant.answer_with_intent(
                "price_stock",
                state.get("routed_query") or state["query"],
                history=state.get("history", []),
            ),
        }

    def recommendation_agent(state: GPFarmState) -> GPFarmState:
        return {
            **state,
            "answer": assistant.answer_with_intent(
                "recommendation",
                state.get("routed_query") or state["query"],
                history=state.get("history", []),
            ),
        }

    def brand_contact_agent(state: GPFarmState) -> GPFarmState:
        return {
            **state,
            "answer": assistant.answer_with_intent(
                "brand_contact",
                state.get("routed_query") or state["query"],
                history=state.get("history", []),
            ),
        }

    def route_by_intent(state: GPFarmState) -> str:
        return _safe_intent(state.get("intent", "product_info"))

    graph.add_node("orchestrator_agent", orchestrator_agent)
    graph.add_node("product_info_agent", product_info_agent)
    graph.add_node("price_stock_agent", price_stock_agent)
    graph.add_node("recommendation_agent", recommendation_agent)
    graph.add_node("brand_contact_agent", brand_contact_agent)

    graph.set_entry_point("orchestrator_agent")
    graph.add_conditional_edges(
        "orchestrator_agent",
        route_by_intent,
        {
            "product_info": "product_info_agent",
            "price_stock": "price_stock_agent",
            "recommendation": "recommendation_agent",
            "brand_contact": "brand_contact_agent",
        },
    )
    graph.add_edge("product_info_agent", END)
    graph.add_edge("price_stock_agent", END)
    graph.add_edge("recommendation_agent", END)
    graph.add_edge("brand_contact_agent", END)

    return graph.compile()
