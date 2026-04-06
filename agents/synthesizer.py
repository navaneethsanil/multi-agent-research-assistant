import logging
from functools import lru_cache

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from graph.state import AgentState
from utils import initialize_llm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are an expert research synthesizer AI.

Your job is to produce a **single, well-structured synthesis** from two research sources
(web search results and ArXiv papers) for a given user query.

## Output Format (follow strictly)

### 📌 Summary
A concise 2–3 sentence overview answering the user's query directly.

### 🔍 Key Findings
- Bullet-point the most important facts, insights, and technical details.
- Merge overlapping information from both sources intelligently (no duplication).
- Clearly distinguish between general knowledge (web) and academic insights (ArXiv) where relevant.

### 📚 Technical Deep Dive (if applicable)
Provide any formulas, methodologies, architectures, or detailed technical content found in
the ArXiv results that enrich the answer beyond general web content.

### 💡 Conclusion
A 1-2 sentence takeaway or actionable insight based on the combined research.

---

## Rules
- Do NOT fabricate or infer information beyond what is provided in the sources.
- If a source has no useful content, explicitly state: "No relevant content from [source]."
- Use clear, precise language. Avoid filler phrases like "It is worth noting that...".
- Keep the total response focused and scannable.

---

## Sources

<web_search_result>
{web_search_result}
</web_search_result>

<arxiv_result>
{arxiv_result}
</arxiv_result>
"""

HUMAN_PROMPT = """
User Query: {query}

Using ONLY the sources provided above, produce a precise synthesis following the
output format specified in your instructions.
"""

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", HUMAN_PROMPT),
])


# ---------------------------------------------------------------------------
# Lazy singleton — chain is built on first call, not at import time.
# Defers initialize_llm() to avoid silent import-time crashes if the
# LLM backend is unavailable when the module is first loaded.
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _get_chain():
    """Build and cache the synthesis chain: prompt | llm | str parser."""
    return _PROMPT | initialize_llm() | StrOutputParser()


def synthesizer_agent(state: AgentState) -> dict:
    """LangGraph node — synthesize web and ArXiv results into a structured response.

    Invokes the cached LLM chain with the query and both source payloads.
    Falls back to safe default strings for any missing state keys so the
    prompt is always fully populated.

    Args:
        state: Current graph state; expected keys:
            - ``query``             – original user question.
            - ``web_search_result`` – output from ``web_search_agent``.
            - ``arxiv_result``      – output from ``arxiv_agent``.

    Returns:
        Partial state update: ``{"response": <str>}``.
        On failure, the value contains a human-readable error message.
    """
    query        = state.get("query") or "No query provided."
    web_result   = state.get("web_search_result") or "No web search results available."
    arxiv_result = state.get("arxiv_result") or "No ArXiv results available."

    try:
        logger.info("synthesizer_agent running for query: '%s'", query)

        response = _get_chain().invoke({
            "query": query,
            "web_search_result": web_result,
            "arxiv_result": arxiv_result,
        })

        logger.info("synthesizer_agent completed for query: '%s'", query)
        return {"response": response}

    except Exception as e:
        logger.exception("synthesizer_agent failed: %s", e)
        return {"response": f"An error occurred during synthesis: {str(e)}"}