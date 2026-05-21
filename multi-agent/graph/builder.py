from langgraph.graph import END, StateGraph

from agents.analyst_agent import analyst_agent
from agents.news_agent import news_agent
from agents.price_agent import price_agent
from state import TradingState


def should_analyze(state: TradingState) -> str:
    return "analyst_agent" if state.get("price_data") else "output_node"


def output_node(state: TradingState) -> TradingState:
    return state


def build_graph():
    graph = StateGraph(TradingState)
    graph.add_node("price_agent", price_agent)
    graph.add_node("news_agent", news_agent)
    graph.add_node("analyst_agent", analyst_agent)
    graph.add_node("output_node", output_node)

    graph.set_entry_point("price_agent")
    graph.add_conditional_edges(
        "price_agent",
        should_analyze,
        {
            "analyst_agent": "news_agent",
            "output_node": "output_node",
        },
    )
    graph.add_edge("news_agent", "analyst_agent")
    graph.add_edge("analyst_agent", "output_node")
    graph.add_edge("output_node", END)

    return graph.compile()
