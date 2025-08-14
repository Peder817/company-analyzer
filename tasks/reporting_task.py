import re
from crewai import Task, Agent
from agents.agents.report_utils import format_report_md  # harmless cleanup util

# Optional: keep the old single-task API but make it explicit it shouldn't be used.
def create_reporting_task(*args, **kwargs):
    raise NotImplementedError(
        "create_reporting_task is deprecated. Use create_chunked_reporting_tasks() "
        "which creates only Executive Summary and Recommendations tasks."
    )

def _dependency_snippets(dependencies) -> str:
    """Collect short, cleaned excerpts from upstream tasks."""
    parts = []
    for dep in dependencies or []:
        out = getattr(dep, "output", None)
        if not out:
            continue
        s = getattr(out, "raw", None)
        s = s if isinstance(s, str) else str(out)
        if len(s) > 1200:
            s = s[:1200] + "... [truncated]"
        s = format_report_md(s)  # light cleanup (e.g., fix malformed md)
        role = getattr(getattr(dep, "agent", None), "role", "previous task")
        parts.append(f"From {role}:\n{s}")
    return "\n\n".join(parts) if parts else "No prior text."

def _latest_quarter_from_sources(sources) -> str:
    """Try to detect 'Qx 20xx' in sources; fall back to a generic label."""
    pattern = re.compile(r"Q[1-4]\s?20\d{2}", re.IGNORECASE)
    for src in sources or []:
        m = pattern.search(str(src))
        if m:
            return m.group(0).replace(" ", "")
    return "the most recent quarter"

def create_chunked_reporting_tasks(
    agent: Agent,
    company_name: str,
    dependencies: list | None = None,
    sources: list | None = None,
):
    """
    Minimal, high-precision reporting:
    - Task 1: Executive Summary (2–3 paragraphs), grounded strictly in inputs.
    - Task 2: Recommendations (3–4 bullets), grounded strictly in inputs.

    Key Research Insights, Financial Analysis Highlights, and Sources are
    assembled deterministically in main.py and are NOT written by this agent.
    """
    dependencies = dependencies or []
    sources = sources or []

    dep_texts = _dependency_snippets(dependencies)
    latest_quarter = _latest_quarter_from_sources(sources)

    # -------------------------
    # Task 1: Executive Summary
    # -------------------------
    t1_desc = (
        f"TITLE: {company_name} Financial Performance Report for {latest_quarter}\n\n"
        f"Write the **Executive Summary** in 2–3 short paragraphs.\n"
        f"GROUND RULES:\n"
        f"- Use ONLY facts present in the INPUT below. Do NOT invent numbers or figures.\n"
        f"- Prefer concise sentences and concrete figures already present.\n"
        f"- Do NOT include any other section (no Key Insights, no Highlights, no Sources).\n"
        f"- No extra headings besides 'Executive Summary'.\n\n"
        f"OUTPUT FORMAT (exactly):\n"
        f"Executive Summary\n"
        f"<paragraph 1>\n\n"
        f"<paragraph 2 (optionally 3)>\n\n"
        f"--- End of Executive Summary ---\n\n"
        f"INPUT:\n{dep_texts}"
    )
    t1 = Task(
        description=t1_desc,
        agent=agent,
        expected_output="Executive Summary (2–3 paragraphs) ending with '--- End of Executive Summary ---'.",
        dependencies=dependencies,
        sources=sources,  # for context only; the agent must not list sources
    )

    # -------------------------
    # Task 2: Recommendations
    # -------------------------
    t2_desc = (
        f"Write **Recommendations** (3–4 actionable bullets) grounded ONLY in INPUT below.\n"
        f"GROUND RULES:\n"
        f"- No invented facts; tie each recommendation to a driver seen in INPUT.\n"
        f"- One line per bullet; start each with '- '. Keep it practical and specific.\n"
        f"- Do NOT include any other section (no Executive Summary text, no Insights/Highlights/Sources).\n\n"
        f"OUTPUT FORMAT (exactly):\n"
        f"Recommendations\n"
        f"- <bullet 1>\n"
        f"- <bullet 2>\n"
        f"- <bullet 3>\n"
        f"(- <bullet 4> optional)\n\n"
        f"--- End of Recommendations ---\n\n"
        f"INPUT:\n{dep_texts}"
    )
    t2 = Task(
        description=t2_desc,
        agent=agent,
        expected_output="Recommendations list (3–4 bullets) ending with '--- End of Recommendations ---'.",
        dependencies=dependencies,
        sources=sources,  # context only
    )

    return [t1, t2]








