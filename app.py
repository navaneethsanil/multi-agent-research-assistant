"""
Multi-Agent Research Assistant — Streamlit UI (Animated Pipeline)
"""

import re as _re
import time
import html as html_lib
import streamlit as st
from graph.state import AgentState
from graph.workflow import graph


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .section-label {
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
        text-transform: uppercase; color: rgba(128,128,128,0.55); margin: 0 0 0.85rem;
    }
    .timeline { display: flex; flex-direction: column; gap: 0; }
    .step-row { display: flex; align-items: flex-start; gap: 14px; position: relative; }
    .step-track { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; width: 28px; }
    .step-icon {
        width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0; position: relative; z-index: 1;
        transition: background .3s, border-color .3s;
    }
    .step-icon.idle    { background: rgba(128,128,128,.07); border: 1.5px solid rgba(128,128,128,.2); }
    .step-icon.running { background: #E6F1FB; border: 1.5px solid #378ADD; }
    .step-icon.done    { background: #EAF3DE; border: 1.5px solid #639922; }
    .step-icon.error   { background: #FCEBEB; border: 1.5px solid #E24B4A; }
    .step-connector { width: 1.5px; flex: 1; min-height: 16px; background: rgba(128,128,128,.18); margin: 2px 0; }
    .step-body { flex: 1; padding-bottom: 20px; }
    .step-header { display: flex; align-items: center; gap: 8px; min-height: 28px; }
    .step-name { font-size: 13px; font-weight: 500; color: rgba(200,205,210,.92); }
    .step-badge {
        font-size: 10px; font-weight: 500; letter-spacing: .04em;
        padding: 2px 8px; border-radius: 999px;
        display: inline-flex; align-items: center; gap: 4px;
    }
    .sub-badge {
        font-size: 9px; font-weight: 500; letter-spacing: .04em;
        padding: 1px 6px; border-radius: 999px;
        display: inline-flex; align-items: center; gap: 3px;
    }
    .badge-idle    { background:rgba(128,128,128,.08); color:rgba(128,128,128,.65); border:0.5px solid rgba(128,128,128,.18); }
    .badge-running { background:#E6F1FB; color:#185FA5; border:0.5px solid #B5D4F4; }
    .badge-done    { background:#EAF3DE; color:#3B6D11; border:0.5px solid #C0DD97; }
    .badge-error   { background:#FCEBEB; color:#A32D2D; border:0.5px solid #F7C1C1; }
    .progress-bar-wrap { height: 2px; background: rgba(128,128,128,.12); border-radius: 2px; margin-top: 6px; overflow: hidden; }
    .progress-bar { height: 100%; width: 0%; border-radius: 2px; transition: width .4s ease; }
    .progress-bar.running { background: #378ADD; }
    .progress-bar.done    { background: #639922; width: 100% !important; }
    .progress-bar.error   { background: #E24B4A; }
    .parallel-row { display: flex; gap: 12px; width: 100%; margin-top: 10px; }
    .parallel-col { flex: 1; min-width: 0; }
    .sub-label { font-size: 11px; color: rgba(128,128,128,.6); margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
    .step-card {
        border-radius: 8px; border: 0.5px solid rgba(128,128,128,.15);
        background: rgba(128,128,128,.04); overflow: hidden;
        max-height: 0; opacity: 0;
        transition: max-height .5s cubic-bezier(.4,0,.2,1), opacity .35s ease;
    }
    .step-card.visible { max-height: 300px; opacity: 1; }
    .step-card-inner {
        padding: .65rem .9rem; font-size: 12.5px; line-height: 1.65;
        color: rgba(180,180,185,.85); white-space: pre-wrap;
        word-break: break-word; max-height: 280px; overflow-y: auto;
    }
    .step-meta { font-size: 11px; color: rgba(128,128,128,.5); margin-top: 2px; }
    .spinner {
        width: 10px; height: 10px; border-radius: 50%;
        border: 1.5px solid transparent; border-top-color: #378ADD;
        animation: spin .7s linear infinite; flex-shrink: 0;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .check-svg { width:11px; height:11px; flex-shrink:0; }
    .dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
    .dot-idle  { background: rgba(128,128,128,.4); }
    .dot-error { background: #E24B4A; }
    .pipeline-step { display:flex; align-items:flex-start; gap:10px; padding:6px 0; }
    .pipeline-dot  { width:8px; height:8px; border-radius:50%; margin-top:5px; flex-shrink:0; }
    .pipeline-line { width:1px; height:16px; background:rgba(128,128,128,.2); margin-left:3px; }
    .pipeline-step-label { font-size:.8rem; color:rgba(180,180,185,.8); }
    .pipeline-step-sub   { font-size:.7rem; color:rgba(128,128,128,.5); margin-top:1px; }
    .stTextArea > label {
        font-size: 0.82rem !important; font-weight: 500 !important;
        letter-spacing: 0.03em !important; color: rgba(128,128,128,.75) !important;
        text-transform: uppercase !important;
    }
    .debug-box {
        background: rgba(128,128,128,.06); border: 0.5px solid rgba(128,128,128,.2);
        border-radius: 8px; padding: .75rem 1rem; font-size: 11px;
        font-family: monospace; color: rgba(180,180,185,.75);
        white-space: pre-wrap; margin-top: .5rem;
    }

    /* ── Elegant Final Answer ─────────────────────────────────────────────── */
    .fa-card {
        background: rgba(255,255,255,.03);
        border: 0.5px solid rgba(128,128,128,.15);
        border-radius: 12px;
        overflow: hidden;
        margin-top: 1.25rem;
    }
    .fa-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: .75rem 1.1rem;
        border-bottom: 0.5px solid rgba(128,128,128,.12);
        background: rgba(128,128,128,.04);
    }
    .fa-header-left { display: flex; align-items: center; gap: 10px; }
    .fa-icon {
        width: 26px; height: 26px; border-radius: 50%;
        background: #EAF3DE; border: 0.5px solid #C0DD97;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .fa-title   { font-size: 12.5px; font-weight: 500; color: rgba(220,225,220,.92); }
    .fa-subtitle{ font-size: 11px; color: rgba(128,128,128,.55); margin-top: 1px; }
    .fa-pill {
        font-size: 11px; font-weight: 500; padding: 2px 9px; border-radius: 999px;
        background: #EAF3DE; color: #3B6D11; border: 0.5px solid #C0DD97;
        display: inline-flex; align-items: center; gap: 4px;
    }
    .fa-body {
        padding: 1.1rem 1.4rem;
        font-size: 14px; line-height: 1.8; color: rgba(215,220,215,.9);
    }
    .fa-body h1, .fa-body h2, .fa-body h3 {
        font-weight: 500; margin: 1.2rem 0 .5rem; color: rgba(230,235,230,.95);
    }
    .fa-body h2 { font-size: 15px; }
    .fa-body h3 { font-size: 13.5px; }
    .fa-body h2:first-child, .fa-body h3:first-child { margin-top: 0; }
    .fa-body p  { margin: 0 0 .8rem; }
    .fa-body p:last-child { margin-bottom: 0; }
    .fa-body ul, .fa-body ol { padding-left: 1.35rem; margin: 0 0 .8rem; }
    .fa-body li { margin-bottom: 3px; }
    .fa-body strong { font-weight: 500; color: rgba(235,240,235,.95); }
    .fa-body code {
        font-family: monospace; font-size: 12px;
        background: rgba(128,128,128,.12); border: 0.5px solid rgba(128,128,128,.2);
        border-radius: 4px; padding: 1px 5px;
    }
    .fa-body blockquote {
        border-left: 2px solid rgba(99,153,34,.5);
        margin: 0 0 .8rem; padding: .45rem .9rem;
        color: rgba(180,185,180,.8); font-size: 13px; border-radius: 0;
    }
    .fa-body hr { border: none; border-top: 0.5px solid rgba(128,128,128,.15); margin: .9rem 0; }
    .fa-footer {
        display: flex; align-items: center; gap: 8px;
        padding: .55rem 1.1rem;
        border-top: 0.5px solid rgba(128,128,128,.12);
        background: rgba(128,128,128,.03);
    }
    .fa-src-dot   { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
    .fa-src-label { font-size: 11px; color: rgba(128,128,128,.5); }
    .fa-src-sep   { font-size: 11px; color: rgba(128,128,128,.25); margin: 0 2px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<p style='font-size:1.15rem;font-weight:600;margin-bottom:2px;'>Research Assistant</p>"
        "<p style='font-size:0.75rem;color:rgba(128,128,128,.6);margin-top:0;'>LangGraph · Multi-agent</p>",
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("<p class='section-label'>Pipeline</p>", unsafe_allow_html=True)
    # Static pipeline topology diagram shown in the sidebar
    st.markdown(
        """
        <div>
          <div class="pipeline-step">
            <div class="pipeline-dot" style="background:rgba(128,128,128,.4)"></div>
            <div><div class="pipeline-step-label">Start</div></div>
          </div>
          <div class="pipeline-line"></div>
          <div style="display:flex;gap:12px;padding:4px 0;">
            <div class="pipeline-step">
              <div class="pipeline-dot" style="background:#5b8dee"></div>
              <div><div class="pipeline-step-label">Web search</div>
                   <div class="pipeline-step-sub">Tavily / SerpAPI</div></div>
            </div>
            <div class="pipeline-step">
              <div class="pipeline-dot" style="background:#e8834a"></div>
              <div><div class="pipeline-step-label">Arxiv</div>
                   <div class="pipeline-step-sub">arxiv.org</div></div>
            </div>
          </div>
          <div class="pipeline-line"></div>
          <div class="pipeline-step">
            <div class="pipeline-dot" style="background:#3cba7a"></div>
            <div><div class="pipeline-step-label">Synthesizer</div>
                 <div class="pipeline-step-sub">Merges findings</div></div>
          </div>
          <div class="pipeline-line"></div>
          <div class="pipeline-step">
            <div class="pipeline-dot" style="background:rgba(128,128,128,.4)"></div>
            <div><div class="pipeline-step-label">End</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("<p class='section-label'>Settings</p>", unsafe_allow_html=True)
    show_raw   = st.toggle("Show raw agent state",  value=False)
    show_debug = st.toggle("Show key diagnostics",   value=False)
    st.divider()
    st.markdown(
        "<p style='font-size:0.7rem;color:rgba(128,128,128,.4);'>LangGraph + Streamlit</p>",
        unsafe_allow_html=True,
    )


# ── Session state ──────────────────────────────────────────────────────────────
# Initialise once per browser session; preserves history across re-runs
for key, default in {"history": [], "running": False}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.6rem;font-weight:600;margin-bottom:4px;'>"
    "Multi-agent research assistant</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='font-size:0.88rem;color:rgba(128,128,128,.65);margin-bottom:0;'>"
    "Web search and Arxiv agents run in parallel — synthesizer merges their findings."
    "</p>",
    unsafe_allow_html=True,
)
st.divider()


# ── HTML helpers ───────────────────────────────────────────────────────────────
def _dot(cls: str) -> str:
    return f'<div class="dot {cls}"></div>'

def _spinner() -> str:
    return '<div class="spinner"></div>'

def _check() -> str:
    return (
        '<svg class="check-svg" viewBox="0 0 12 12" fill="none">'
        '<polyline points="2,6 5,9 10,3" stroke="#639922" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )

def _icon(state: str) -> str:
    """Return the appropriate inline HTML icon for a given step state."""
    return {
        "idle":    _dot("dot-idle"),
        "running": _spinner(),
        "done":    _check(),
        "error":   _dot("dot-error"),
    }.get(state, _dot("dot-idle"))

def _label(state: str) -> str:
    return {"idle": "Waiting", "running": "Running",
            "done": "Done", "error": "Error"}.get(state, state)

def _badge(state: str, small: bool = False) -> str:
    """Render a coloured status badge (full-size or sub-badge variant)."""
    cls = "sub-badge" if small else "step-badge"
    return (
        f'<span class="{cls} badge-{state}">'
        f'{_icon(state)}&nbsp;{_label(state)}</span>'
    )

def _progress_bar(state: str, pct: int = 0) -> str:
    """Render a thin progress bar that reflects the current step state."""
    if state == "done":
        return '<div class="progress-bar-wrap"><div class="progress-bar done"></div></div>'
    if state in ("running", "error"):
        return (
            f'<div class="progress-bar-wrap">'
            f'<div class="progress-bar {state}" style="width:{pct}%"></div></div>'
        )
    return '<div class="progress-bar-wrap"><div class="progress-bar"></div></div>'

def _safe(text: str) -> str:
    """HTML-escape user / agent content before injecting into markup."""
    return html_lib.escape(text)

def _card(content: str, visible: bool = False) -> str:
    """Render a collapsible content card; animated open when ``visible=True``."""
    vis   = " visible" if visible else ""
    inner = (
        f'<div class="step-card-inner">{_safe(content)}</div>'
        if content else ""
    )
    return f'<div class="step-card{vis}">{inner}</div>'

def _sub_col(sub_state: str, label: str, content: str) -> str:
    """Render one column of the parallel-fetch row (web or arxiv)."""
    return (
        f'<div class="parallel-col">'
        f'<div class="sub-label">{_badge(sub_state, small=True)}'
        f'<span>{_safe(label)}</span></div>'
        f'{_card(content, visible=bool(content))}'
        f'</div>'
    )


# ── The one function that writes to a placeholder ──────────────────────────────
def _render(placeholder, html: str) -> None:
    """Write HTML into a Streamlit placeholder with unsafe_allow_html enabled."""
    placeholder.markdown(html, unsafe_allow_html=True)


# ── Timeline builder ───────────────────────────────────────────────────────────
def render_timeline(
    *,
    fetch_state:   str = "idle",
    fetch_pct:     int = 0,
    ws_state:      str = "idle",
    ws_content:    str = "",
    ax_state:      str = "idle",
    ax_content:    str = "",
    synth_state:   str = "idle",
    synth_pct:     int = 0,
    end_state:     str = "idle",
) -> str:
    """Build the full animated pipeline timeline as an HTML string.

    Each keyword arg maps to one visual step or sub-agent in the timeline.
    State values: ``"idle"`` | ``"running"`` | ``"done"`` | ``"error"``.

    Args:
        fetch_state:  Overall state of the parallel-fetch step.
        fetch_pct:    Progress bar percentage for the fetch step (0–100).
        ws_state:     State of the web-search sub-agent.
        ws_content:   Truncated output to display in the web-search card.
        ax_state:     State of the ArXiv sub-agent.
        ax_content:   Truncated output to display in the ArXiv card.
        synth_state:  State of the synthesizer step.
        synth_pct:    Progress bar percentage for the synthesizer (0–100).
        end_state:    State of the terminal END node.

    Returns:
        Self-contained HTML string ready for ``st.markdown(..., unsafe_allow_html=True)``.
    """
    return (
        '<div class="timeline">'

        # ── Step 1: Parallel fetch ──────────────────────────────────────
        '<div class="step-row">'
        '<div class="step-track">'
        f'<div class="step-icon {fetch_state}">{_icon(fetch_state)}</div>'
        '<div class="step-connector"></div>'
        '</div>'
        '<div class="step-body">'
        '<div class="step-header">'
        '<span class="step-name">Parallel fetch</span>'
        f'{_badge(fetch_state)}'
        '</div>'
        '<div class="step-meta">Web search + Arxiv running concurrently</div>'
        f'{_progress_bar(fetch_state, fetch_pct)}'
        '<div class="parallel-row">'
        f'{_sub_col(ws_state, "Web search", ws_content)}'
        f'{_sub_col(ax_state, "Arxiv",      ax_content)}'
        '</div>'
        '</div>'
        '</div>'

        # ── Step 2: Synthesizer ─────────────────────────────────────────
        '<div class="step-row">'
        '<div class="step-track">'
        f'<div class="step-icon {synth_state}">{_icon(synth_state)}</div>'
        '<div class="step-connector"></div>'
        '</div>'
        '<div class="step-body">'
        '<div class="step-header">'
        '<span class="step-name">Synthesizer</span>'
        f'{_badge(synth_state)}'
        '</div>'
        '<div class="step-meta">Merging findings from all agents</div>'
        f'{_progress_bar(synth_state, synth_pct)}'
        '</div>'
        '</div>'

        '</div>'   # .timeline
    )


# ── Markdown → HTML (lightweight, no external deps) ───────────────────────────
def _md_to_html(text: str) -> str:
    """Convert a Markdown subset to safe HTML for the final answer card.

    Supported syntax: h1–h3, **bold**, ``inline code``, ``---`` (hr),
    ``>`` blockquote, unordered lists (``-``, ``*``, ``+``),
    ordered lists, and plain paragraphs.

    All text is HTML-escaped *before* inline pattern substitution to
    prevent injection through agent-generated content.

    Args:
        text: Raw Markdown string from the synthesizer agent.

    Returns:
        HTML string safe for injection into ``unsafe_allow_html`` blocks.
    """
    lines = text.split("\n")
    out: list[str] = []
    in_ul = in_ol = in_bq = False
    buf_p: list[str] = []

    def flush_p() -> None:
        if buf_p:
            content = " ".join(buf_p).strip()
            if content:
                out.append(f"<p>{_inline(content)}</p>")
            buf_p.clear()

    def close_blocks() -> None:
        nonlocal in_ul, in_ol, in_bq
        if in_ul:  out.append("</ul>");         in_ul = False
        if in_ol:  out.append("</ol>");         in_ol = False
        if in_bq:  out.append("</blockquote>"); in_bq = False

    def _inline(s: str) -> str:
        """Escape then apply bold and inline-code substitutions."""
        s = html_lib.escape(s)
        s = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = _re.sub(r"`(.+?)`",        r"<code>\1</code>",    s)
        return s

    for raw in lines:
        line = raw.rstrip()

        # Headings
        hm = _re.match(r"^(#{1,3})\s+(.*)", line)
        if hm:
            flush_p(); close_blocks()
            lvl = len(hm.group(1))
            out.append(f"<h{lvl}>{_inline(hm.group(2))}</h{lvl}>")
            continue

        # Horizontal rule
        if _re.match(r"^[-*_]{3,}$", line.strip()):
            flush_p(); close_blocks()
            out.append("<hr>")
            continue

        # Blockquote
        bqm = _re.match(r"^>\s?(.*)", line)
        if bqm:
            flush_p()
            if in_ul: out.append("</ul>"); in_ul = False
            if in_ol: out.append("</ol>"); in_ol = False
            if not in_bq:
                out.append("<blockquote>"); in_bq = True
            out.append(f"<p>{_inline(bqm.group(1))}</p>")
            continue
        elif in_bq:
            out.append("</blockquote>"); in_bq = False

        # Unordered list
        ulm = _re.match(r"^[\-\*\+]\s+(.*)", line)
        if ulm:
            flush_p()
            if in_ol: out.append("</ol>"); in_ol = False
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append(f"<li>{_inline(ulm.group(1))}</li>")
            continue

        # Ordered list
        olm = _re.match(r"^\d+\.\s+(.*)", line)
        if olm:
            flush_p()
            if in_ul: out.append("</ul>"); in_ul = False
            if not in_ol: out.append("<ol>"); in_ol = True
            out.append(f"<li>{_inline(olm.group(1))}</li>")
            continue

        # Blank line — flush buffered paragraph and close any open blocks
        if not line.strip():
            flush_p(); close_blocks()
            continue

        # Plain paragraph text
        if in_ul or in_ol:
            flush_p(); close_blocks()
        buf_p.append(line)

    flush_p()
    close_blocks()
    return "\n".join(out)


# ── Elegant final answer renderer ──────────────────────────────────────────────
def render_final_answer(text: str, elapsed: float) -> str:
    """Render the synthesized result as a structured card with header and footer.

    Args:
        text:    Markdown-formatted synthesis from ``synthesizer_agent``.
        elapsed: Total pipeline wall-clock time in seconds (shown in header pill).

    Returns:
        Self-contained HTML card string.
    """
    body_html = _md_to_html(text)

    clock_svg = (
        '<svg width="10" height="10" viewBox="0 0 10 10" fill="none">'
        '<circle cx="5" cy="5" r="4" stroke="#3B6D11" stroke-width="1.2"/>'
        '<polyline points="5,3 5,5.5 6.5,6.5" stroke="#3B6D11" '
        'stroke-width="1.2" stroke-linecap="round"/>'
        "</svg>"
    )
    check_svg = (
        '<svg width="12" height="12" viewBox="0 0 12 12" fill="none">'
        '<polyline points="2,6 5,9 10,3" stroke="#3B6D11" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
        "</svg>"
    )

    return (
        '<div class="fa-card">'

        # Header: icon, title/subtitle, elapsed-time pill
        '<div class="fa-header">'
        '<div class="fa-header-left">'
        f'<div class="fa-icon">{check_svg}</div>'
        "<div>"
        '<div class="fa-title">Final Result</div>'
        '<div class="fa-subtitle">Web search + Arxiv &nbsp;&middot;&nbsp; merged findings</div>'
        "</div>"
        "</div>"
        f'<span class="fa-pill">{clock_svg}&nbsp;{elapsed}s</span>'
        "</div>"

        # Body: Markdown-rendered synthesis
        f'<div class="fa-body">{body_html}</div>'

        # Footer: source attribution dots
        '<div class="fa-footer">'
        '<div class="fa-src-dot" style="background:#5b8dee;"></div>'
        '<span class="fa-src-label">Web search</span>'
        '<span class="fa-src-sep">&middot;</span>'
        '<div class="fa-src-dot" style="background:#e8834a;"></div>'
        '<span class="fa-src-label">Arxiv</span>'
        "</div>"

        "</div>"
    )


# ── State key resolver ─────────────────────────────────────────────────────────
# Candidate keys checked in priority order when extracting agent outputs
# from the flattened graph state. Extend these tuples if node output keys change.
_WEB_KEYS   = ("web_search_result", "web_result", "web_search", "web_output", "web")
_ARXIV_KEYS = ("arxiv_result", "arxiv_output", "arxiv_search", "arxiv")
_SYNTH_KEYS = ("response", "synthesis", "synth_result", "final_response",
               "synthesized_result", "output", "result")


def _to_str(v) -> str:
    """Coerce any agent output value to a plain string.

    Handles: ``None``, ``str``, LangChain message objects (``content``
    attribute), lists (uses last element), and dicts (probes common
    content keys, then falls back to ``messages``).
    """
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if hasattr(v, "content"):
        return str(v.content).strip()
    if isinstance(v, list) and v:
        return _to_str(v[-1])
    if isinstance(v, dict):
        for k in ("content", "output", "result", "text", "answer"):
            if v.get(k):
                return _to_str(v[k])
        msgs = v.get("messages")
        if msgs and isinstance(msgs, list):
            return _to_str(msgs[-1])
        return str(v)
    return str(v).strip()


def _extract(mapping: dict, candidates: tuple) -> str:
    """Return the first non-empty string value found among ``candidates`` keys."""
    for key in candidates:
        val = mapping.get(key)
        if val:
            result = _to_str(val)
            if result:
                return result
    return ""


def _flatten_chunk(chunk: dict) -> dict:
    """Unwrap a LangGraph stream chunk from ``{node_name: {k: v}}`` to ``{k: v}``.

    Also preserves the raw node-keyed entry so node names remain queryable.
    """
    flat: dict = {}
    for node_name, node_output in chunk.items():
        if isinstance(node_output, dict):
            flat.update(node_output)
            flat[node_name] = node_output
        else:
            flat[node_name] = node_output
    return flat


def _animated_pct(elapsed: float, budget: float) -> int:
    """Map elapsed time to a progress percentage using an ease-out curve.

    Approaches 92 % asymptotically so the bar never appears to "finish"
    before the actual result arrives.
    """
    frac = min(elapsed / max(budget, 0.001), 1.0)
    return int(92 * (1 - (1 - frac) ** 2))


# ── Main form ──────────────────────────────────────────────────────────────────
with st.form("query_form", clear_on_submit=False):
    query = st.text_area(
        "Research question",
        placeholder="e.g. What are the latest advances in multimodal RAG systems?",
        height=96,
    )
    submitted = st.form_submit_button(
        "Run research pipeline",
        use_container_width=True,
        disabled=st.session_state.running,
    )

if submitted and query.strip():
    st.session_state.running = True
    st.divider()

    st.markdown("<p class='section-label'>Agent activity</p>", unsafe_allow_html=True)

    # Dedicated placeholders let us overwrite each region independently
    ph_timeline = st.empty()
    ph_debug    = st.empty()
    ph_final    = st.empty()

    # Render idle baseline before the graph starts streaming
    _render(ph_timeline, render_timeline())

    t0 = time.perf_counter()

    # Expected wall-clock budgets used to drive the animated progress bars
    FETCH_BUDGET = 4.0
    SYNTH_BUDGET = 2.5

    web_str = arxiv_str = synth_str = ""
    final_flat: dict = {}
    all_chunks: list = []

    try:
        initial_state: AgentState = {"query": query}

        for chunk in graph.stream(initial_state, stream_mode="updates"):
            elapsed = time.perf_counter() - t0
            all_chunks.append(chunk)

            # Flatten node-namespaced chunk into a single key-value mapping
            flat = _flatten_chunk(chunk)
            final_flat.update(flat)

            # Extract outputs incrementally; retain last non-empty value
            web_str   = _extract(final_flat, _WEB_KEYS)   or web_str
            arxiv_str = _extract(final_flat, _ARXIV_KEYS) or arxiv_str
            synth_str = _extract(final_flat, _SYNTH_KEYS) or synth_str

            fetch_done = bool(web_str and arxiv_str)
            synth_done = bool(synth_str)

            if show_debug:
                _render(
                    ph_debug,
                    f'<div class="debug-box">'
                    f'Flat keys: {list(final_flat.keys())}\n'
                    f'web   = {repr(web_str[:80])   if web_str   else "EMPTY"}\n'
                    f'arxiv = {repr(arxiv_str[:80]) if arxiv_str else "EMPTY"}\n'
                    f'synth = {repr(synth_str[:80]) if synth_str else "EMPTY"}'
                    f'</div>',
                )

            # Update timeline to reflect the latest pipeline state
            if synth_done:
                _render(ph_timeline, render_timeline(
                    fetch_state="done",
                    ws_state="done",  ws_content=web_str,
                    ax_state="done",  ax_content=arxiv_str,
                    synth_state="done",
                    end_state="done",
                ))

            elif fetch_done:
                synth_pct = _animated_pct(elapsed - FETCH_BUDGET, SYNTH_BUDGET)
                _render(ph_timeline, render_timeline(
                    fetch_state="done",
                    ws_state="done",  ws_content=web_str,
                    ax_state="done",  ax_content=arxiv_str,
                    synth_state="running", synth_pct=synth_pct,
                ))

            else:
                fetch_pct = _animated_pct(elapsed, FETCH_BUDGET)
                _render(ph_timeline, render_timeline(
                    fetch_state="running", fetch_pct=fetch_pct,
                    ws_state="done" if web_str   else "running", ws_content=web_str,
                    ax_state="done" if arxiv_str else "running", ax_content=arxiv_str,
                ))

        # ── Stream finished — render final answer exactly once ──────────
        elapsed_total = round(time.perf_counter() - t0, 2)
        has_web, has_arxiv, has_synth = bool(web_str), bool(arxiv_str), bool(synth_str)

        # Final timeline snapshot — mark failed agents as "error"
        _render(ph_timeline, render_timeline(
            fetch_state="done"  if (has_web or has_arxiv) else "error",
            ws_state="done"     if has_web   else "error",
            ws_content=web_str  or "No output returned.",
            ax_state="done"     if has_arxiv else "error",
            ax_content=arxiv_str or "No output returned.",
            synth_state="done"  if has_synth else "error",
            end_state="done"    if has_synth else "error",
        ))

        if has_synth:
            _render(ph_final, render_final_answer(synth_str, elapsed_total))
        else:
            st.warning(
                f"⚠️ Synthesizer returned no output. "
                f"Keys seen: `{list(final_flat.keys())}`. "
                "Add the correct key to `_SYNTH_KEYS` in app.py."
            )

        if show_raw:
            with st.expander("Raw agent state (all chunks)", expanded=False):
                st.json(all_chunks)

        # Persist to session history for the research history panel below
        st.session_state.history.append({
            "query":     query,
            "web":       web_str,
            "arxiv":     arxiv_str,
            "synthesis": synth_str,
            "elapsed":   elapsed_total,
        })

    except Exception as exc:
        st.error(f"Pipeline error: {exc}")
        _render(ph_timeline, render_timeline(
            fetch_state="error",
            ws_state="error", ws_content=str(exc),
            ax_state="error", ax_content=str(exc),
            synth_state="error", end_state="error",
        ))

    finally:
        st.session_state.running = False
        ph_debug.empty()   # Always clear the transient debug overlay

elif submitted and not query.strip():
    st.warning("Please enter a research question before running.")


# ── Research history ───────────────────────────────────────────────────────────
if st.session_state.history:
    st.divider()
    st.markdown("<p class='section-label'>Research history</p>", unsafe_allow_html=True)

    for entry in reversed(st.session_state.history):
        label = entry["query"][:80] + ("…" if len(entry["query"]) > 80 else "")
        with st.expander(f"{label}  ·  {entry['elapsed']}s", expanded=False):
            t1, t2, t3 = st.tabs(["Synthesis", "Web search", "Arxiv"])
            with t1:
                st.markdown(entry["synthesis"] or "_No synthesis._")
            with t2:
                st.markdown(entry["web"] or "_No web results._")
            with t3:
                st.markdown(entry["arxiv"] or "_No Arxiv results._")

    if st.button("Clear history", use_container_width=False):
        st.session_state.history = []
        st.rerun()