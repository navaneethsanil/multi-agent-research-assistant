import logging
from langchain_community.retrievers import ArxivRetriever

from graph.state import AgentState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton — ArxivRetriever is stateless, safe to reuse
# ---------------------------------------------------------------------------
_retriever = ArxivRetriever(
    load_max_docs=2,       # Limit to 2 papers to stay within context budget
    get_full_documents=False,  # Fetch abstracts only; full PDFs are too large
)

# Per-document character cap to prevent context overflow in downstream nodes
_MAX_CONTENT_LENGTH_PER_DOC = 4000


def arxiv_agent(state: AgentState) -> dict:
    """LangGraph node — retrieve and aggregate ArXiv papers for a given query.

    Fetches up to ``load_max_docs`` papers via ``ArxivRetriever``, formats
    each with its metadata header, and joins them into a single string stored
    in ``arxiv_result``.

    Args:
        state: Current graph state; must contain a non-empty ``query`` key.

    Returns:
        Partial state update: ``{"arxiv_result": <str>}``.
        On failure, the value contains a human-readable error message
        so downstream nodes can degrade gracefully.
    """
    query = state.get("query", "").strip()

    if not query:
        logger.warning("arxiv_agent called with an empty query.")
        return {"arxiv_result": "No query provided to search ArXiv."}

    try:
        logger.info("arxiv_agent fetching papers for query: '%s'", query)
        docs = _retriever.invoke(query)

        if not docs:
            logger.info("No ArXiv documents found for query: '%s'", query)
            return {"arxiv_result": "No relevant research papers found on ArXiv."}

        aggregated_parts = []

        for i, doc in enumerate(docs, start=1):
            title     = doc.metadata.get("Title", f"Document {i}")
            authors   = doc.metadata.get("Authors", "Unknown Authors")
            published = doc.metadata.get("Published", "Unknown Date")
            entry_id  = doc.metadata.get("Entry ID", "N/A")

            content = doc.page_content
            if len(content) > _MAX_CONTENT_LENGTH_PER_DOC:
                content = content[:_MAX_CONTENT_LENGTH_PER_DOC] + "\n... [Content truncated]"

            aggregated_parts.append(
                f"--- Paper {i} ---\n"
                f"Title     : {title}\n"
                f"Authors   : {authors}\n"
                f"Published : {published}\n"
                f"ArXiv ID  : {entry_id}\n\n"
                f"{content}"
            )

        arxiv_result = "\n\n".join(aggregated_parts)

        logger.info(
            "arxiv_agent fetched %d paper(s) for query: '%s'",
            len(docs), query,
        )
        return {"arxiv_result": arxiv_result}

    except Exception as e:
        logger.exception("arxiv_agent failed: %s", e)
        return {"arxiv_result": f"An error occurred while fetching research papers: {str(e)}"}