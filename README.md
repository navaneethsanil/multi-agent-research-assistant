# Multi-Agent Research Assistant

A parallel multi-agent research pipeline that combines real-time web search and ArXiv academic retrieval, synthesized into a structured response — all visualized through an animated Streamlit UI.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Pipeline Walkthrough](#pipeline-walkthrough)
- [Tech Stack](#tech-stack)

---

## Overview

The Multi-Agent Research Assistant is a LangGraph-powered application that orchestrates three specialized AI agents to answer research queries. The web search and ArXiv agents run **in parallel**, and their outputs are merged by a synthesizer agent into a single, well-structured response. The Streamlit frontend streams live pipeline progress to the user with an animated timeline.

---

## Features

- **Parallel agent execution** — web search and ArXiv retrieval run concurrently via LangGraph 
- **ReAct web search** — Tavily-backed agent with grounded, fact-only summarization
- **ArXiv academic retrieval** — fetches and formats up to 2 research paper abstracts
- **LLM synthesis** — structured prompt merges both sources into a scannable report
- **Animated Streamlit UI** — real-time pipeline timeline with per-agent status and progress bars
- **Session history** — persists all queries and results within the browser session
- **Debug mode** — optional raw state and key diagnostic overlays

---

## System Architecture

```
                    ┌─────────────────────────────┐
                    │           START             │
                    └────────────┬────────────────┘
                                 │ 
               ┌─────────────────┴─────────────────┐
               ▼                                   ▼
   ┌───────────────────────┐         ┌───────────────────────┐
   │    web_search_agent   │         │      arxiv_agent      │
   │  Tavily + ReAct (LLM) │         │   ArxivRetriever x2   │
   └───────────┬───────────┘         └───────────┬───────────┘
               │                                 │
               └─────────────┬───────────────────┘
                             │ 
                             ▼
                ┌────────────────────────┐
                │    synthesizer_agent   │
                │  ChatPrompt | LLM | StrOutputParser  │
                └────────────┬───────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │       END       │
                    └─────────────────┘
```

### Shared State (`AgentState`)

| Field               | Type  | Description                              |
|---------------------|-------|------------------------------------------|
| `query`             | `str` | Original user research question          |
| `web_search_result` | `str` | Summarized output from web search agent  |
| `arxiv_result`      | `str` | Aggregated ArXiv paper content           |
| `response`          | `str` | Final synthesized answer                 |

---

## Prerequisites

- Python **3.10+**
- A [Tavily API key](https://tavily.com/) for web search
- An [Anthropic](https://console.anthropic.com/) **or** [OpenAI](https://platform.openai.com/) API key for the LLM

---

## Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/navaneethsanil/multi-agent-research-assistant.git
cd multi-agent-research-assistant

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### `requirements.txt`

```
arxiv>=2.4.1
ipython>=9.12.0
langchain>=1.2.15
langchain-community>=0.4.1
langchain-core>=1.2.26
langchain-mistralai>=1.1.2
langchain-tavily>=0.2.17
langgraph>=1.1.6
pymupdf>=1.27.2.2
python-dotenv>=1.2.2
streamlit>=1.56.0
```

---

## Configuration

Copy `.env.example` to `.env` and populate your credentials:

```bash
cp .env.example .env
```
# Prerequisites note: Ensure your Mistral API key and Tavily API key are configured before running the application.
```env
# .env

# LLM provider — set one
MISTRAL_API_KEY=sk-ant-...

# Model name
MODEL_NAME=mistral-small-latest

# Web search
TAVILY_API_KEY=tvly-...
```

> **Note:** `utils.py → initialize_llm()` reads these variables and returns the appropriate LangChain chat model. Update this function if you switch providers.

---

## Usage

```bash
streamlit run app.py
```

1. Open `http://localhost:8501` in your browser.
2. Enter a research question in the text area.
3. Click **Run research pipeline**.
4. Watch the animated timeline as the agents run in parallel.
5. Review the structured final answer card once synthesis completes.

---

## Pipeline Walkthrough

| Stage | Agent | Tool | Output key |
|-------|-------|------|------------|
| **** | `web_search_agent` | Tavily + ReAct LLM | `web_search_result` |
| **** | `arxiv_agent` | `ArxivRetriever` | `arxiv_result` |
| **** | `synthesizer_agent` | LLM chain | `response` |

### 1. `web_search_agent`
Invokes a `create_react_agent` loop backed by `TavilySearch(max_results=5)`. Extracts the last `AIMessage` from the ReAct trajectory and truncates output to 4 000 characters.

### 2. `arxiv_agent`
Uses `ArxivRetriever(load_max_docs=2, get_full_documents=False)` to fetch paper abstracts. Each document is formatted with its title, authors, publish date, and ArXiv ID, then capped at 4 000 characters.

### 3. `synthesizer_agent`
Feeds both results into a `ChatPromptTemplate` that enforces a structured output format (Summary → Key Findings → Technical Deep Dive → Conclusion). The chain is built lazily via `@lru_cache` to avoid import-time failures.

### Streamlit Streaming
The UI calls `graph.stream(state, stream_mode="updates")` and re-renders the timeline placeholder on every chunk using `st.empty()` + `placeholder.markdown(...)`. Progress bars are driven by an ease-out curve (`_animated_pct`) against expected time budgets.

---

## Tech Stack

| Layer | Library |
|-------|---------|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM abstraction | [LangChain](https://github.com/langchain-ai/langchain) |
| Web search | [Tavily](https://tavily.com/) via `langchain-tavily` |
| Academic search | [ArXiv](https://arxiv.org/) via `langchain-community` |
| LLM backend | Anthropic Claude / OpenAI GPT |
| Frontend | [Streamlit](https://streamlit.io/) |
| Language | Python 3.10+ |
