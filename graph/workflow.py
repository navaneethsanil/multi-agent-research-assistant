from langgraph.graph import START, StateGraph, END
from agents.arxiv import arxiv_agent
from agents.synthesizer import synthesizer_agent
from agents.web_search import web_search_agent
from graph.state import AgentState

# ---------------------------------------------------------------------------
# Graph definition
# Topology: fan-out from START → parallel retrieval → fan-in to synthesizer
#
#   START ──► web_search_agent ──┐
#                                ├──► synthesizer ──► END
#   START ──► arxiv_agent ───────┘
# ---------------------------------------------------------------------------
graph_builder = StateGraph(AgentState)

# --- Nodes ----------------------------------------------------------------
graph_builder.add_node("web_search_agent", web_search_agent)
graph_builder.add_node("arxiv_agent", arxiv_agent)
graph_builder.add_node("synthesizer", synthesizer_agent)

# --- Edges ----------------------------------------------------------------
# Fan-out: both retrieval agents run in parallel from START
graph_builder.add_edge(START, "web_search_agent")
graph_builder.add_edge(START, "arxiv_agent")

# Fan-in: synthesizer waits for both retrieval agents to complete
graph_builder.add_edge("web_search_agent", "synthesizer")
graph_builder.add_edge("arxiv_agent", "synthesizer")

graph_builder.add_edge("synthesizer", END)

# Compile into an executable graph
graph = graph_builder.compile()