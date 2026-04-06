import logging
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent

from graph.state import AgentState
from utils import initialize_llm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons — initialize once, reuse across all invocations
# ---------------------------------------------------------------------------
_llm = initialize_llm()

_tavily_search = TavilySearch(
    max_results=5,
    topic="general",
)

_agent = create_react_agent(
    model=_llm,
    tools=[_tavily_search],
    prompt=(
        "You are a precise research assistant. "
        "Use the web search tool to find accurate, up-to-date information. "
        "Always return a clear, factual summary of your findings. "
        "Do not speculate beyond what the search results say."
    ),
)

# Hard limit to prevent context window overflow in downstream nodes
_MAX_CONTENT_LENGTH = 4000


def _extract_text_from_response(response: dict) -> str:
    """Extract the final AI text content from the ReAct agent's message list.

    Walks the message list in reverse to find the last ``AIMessage``
    with a non-empty string payload, skipping tool-call stubs whose
    ``content`` is empty or a list of tool-call dicts.

    Args:
        response: Raw dict returned by ``_agent.invoke``.
                  Expected shape: ``{"messages": [HumanMessage, ..., AIMessage]}``.

    Returns:
        Stripped text content of the last AI message, or a fallback
        string if no readable message is found.
    """
    messages = response.get("messages", [])
    if not messages:
        return "No response returned from web search agent."

    for msg in reversed(messages):
        content = getattr(msg, "content", None)
        if content and isinstance(content, str) and content.strip():
            return content.strip()

    return "Web search agent did not produce a readable response."


def web_search_agent(state: AgentState) -> dict:
    """LangGraph node — run a Tavily-backed ReAct search and return a summary.

    Args:
        state: Current graph state; must contain a non-empty ``query`` key.

    Returns:
        Partial state update: ``{"web_search_result": <str>}``.
        On failure, the value contains a human-readable error message
        so downstream nodes can degrade gracefully.
    """
    query = state.get("query", "").strip()

    if not query:
        logger.warning("web_search_agent called with an empty query.")
        return {"web_search_result": "No query provided for web search."}

    try:
        logger.info("web_search_agent invoking for query: '%s'", query)

        response = _agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })

        result = _extract_text_from_response(response)

        # Truncate to avoid overwhelming the summarizer's context window
        if len(result) > _MAX_CONTENT_LENGTH:
            result = result[:_MAX_CONTENT_LENGTH] + "\n... [Content truncated]"

        logger.info("web_search_agent completed for query: '%s'", query)
        return {"web_search_result": result}

    except Exception as e:
        logger.exception("web_search_agent failed: %s", e)
        return {"web_search_result": f"An error occurred during web search: {str(e)}"}