from crewai import Task
from crewai import Agent

def create_financial_research_task(
    agent: Agent,
    company_name: str,
    dependencies: list | None = None,
    sources: list | None = None,
):
    if dependencies is None:
        dependencies = []
    if sources is None:
        sources = []

    description = f"""
ROLE
- You are a cautious financial researcher. You MUST NOT invent numbers.

TOOLS
- You MUST call the `financial_data` tool first to fetch structured quarterly financials for {company_name}.
- Then call `web_search` for context (analyst notes, management commentary, recent news).
- Prefer primary sources (10-K/10-Q, earnings releases, investor relations) for the numbers.

OBJECTIVE
- Produce machine-readable quarterly financials (at least the last 8 quarters) PLUS a short human summary.

STRICT REQUIREMENTS
1) QUARTERLY DATA:
   - Provide a JSON object with this shape (omit metrics if truly unavailable, do NOT make them up):
     {{
       "quarterly_financials": {{
         "Total Revenue": {{"Q2 2025": 82000000000, "Q1 2025": 81000000000, ...}},
         "Net Income":    {{"Q2 2025": 20000000000, ...}},
         "EBITDA":        {{"Q2 2025": 30000000000, ...}}
       }},
       "quarters": [
         {{"quarter":"Q2 2025","revenue":82000000000,"net_income":20000000000,"ebitda":30000000000}},
         {{"quarter":"Q1 2025","revenue":81000000000,"net_income":19500000000,"ebitda":29000000000}}
       ],
       "sources": ["https://...", "https://..."]
     }}
   - Quarter labels MUST be "Q# YYYY" (e.g., "Q2 2025").
   - Values MUST be numeric (integers in USD), not strings, no commas.
   - Provide >= 8 quarters when available. If EBITDA missing in sources, omit the key (don't infer).
   - Ensure quarters are consistent across metrics (same set of labels).

2) SOURCING:
   - Every metric series MUST be traceable to cited sources (IR releases, SEC filings, reputable financial data providers).
   - If two sources disagree, prefer the primary source and note the discrepancy.

3) DATA HYGIENE:
   - Do NOT mix annual and quarterly values.
   - Do NOT include ratios or per-share metrics in quarterly_financials (those can be separate).
   - If the tool returns dates (Timestamps), convert them to "Q# YYYY".

OUTPUT FORMAT (return BOTH parts below):
A) HUMAN SUMMARY (markdown, concise, 5–8 bullets).
B) JSON BLOCK (exact markers, valid JSON):
=== QUARTERLY DATA (returned) ===
{{ JSON here exactly as described above }}
=== END ===
""".strip()

    if dependencies:
        dep_outputs = "\n\n".join(
            f"Dependency output from {getattr(dep.agent, 'role', 'previous task')}:\n{getattr(dep, 'output', '')}"
            for dep in dependencies
        )
        description += (
            "\n\nCONTEXT FROM PREVIOUS TASKS\n"
            f"{dep_outputs}"
        )

    expected_output = f"""
- Clear, sourced quarterly financials for {company_name} (>=8 quarters when available).
- Human summary + JSON block exactly between markers.
- Sources list included in the JSON ("sources": [...]).
""".strip()

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        dependencies=dependencies,
        sources=sources,
    )


