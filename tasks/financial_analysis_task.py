from crewai import Task, Agent

def create_financial_analysis_task(
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
- You are a precise financial analyst. Do NOT invent numbers. Prefer primary sources.

INPUTS
- Read all prior task outputs (research & web search) from dependencies.
- If any dependency already contains a QUARTERLY DATA JSON block, reuse it.
- If not, you MUST call the tool named EXACTLY `financial_data` for {company_name} to fetch structured financials.

OBJECTIVE
- Produce a concise financial analysis (3–6 bullets) AND a machine-readable quarterly payload the UI can chart.

DATA RULES
- Quarters must be labeled "Q# YYYY" (e.g., "Q2 2025").
- Values must be integers in USD (no strings, no commas).
- Provide at least the latest 8 quarters when available. If a metric is unavailable, omit it (do NOT infer).
- If the tool returns timestamps, convert to "Q# YYYY".
- If quarterly data is truly unavailable but annual is available, you MAY output FY rows labeled "FY YYYY"; clearly say this in the bullets.

WHAT TO ANALYZE (if data exists)
- Identify latest quarter and same quarter last year (YoY).
- Compute YoY % for Revenue and Net Income when both quarters exist.
- Note EBITDA trend if available (latest vs. prior 3–4 quarters).
- Call out any material changes (mix shift, services vs. hardware, margins) grounded in sources.

OUTPUT FORMAT (return BOTH parts below; markers must be exact):

A) Financial Analysis Highlights (markdown bullets)
Financial Analysis Highlights
- 3–6 concise, numeric bullets (YoY where applicable, explicitly name quarters, e.g., "Revenue Q2 2025 up 5% YoY vs Q2 2024")
- If using FY fallback, state: "Using FY data due to missing quarterly series."
- Include 1 short risk/uncertainty bullet if relevant.
- End with this marker exactly:
--- End of Financial Analysis ---

B) JSON BLOCK (valid JSON only; no trailing commas; DO NOT output "OK")
=== QUARTERLY DATA (returned) ===
{{
  "quarterly_financials": {{
    "Total Revenue": {{"Q2 2025": 82000000000, "Q1 2025": 81000000000}},
    "Net Income":    {{"Q2 2025": 20000000000}},
    "EBITDA":        {{"Q2 2025": 30000000000}}
  }},
  "quarters": [
    {{"quarter":"Q2 2025","revenue":82000000000,"net_income":20000000000,"ebitda":30000000000}},
    {{"quarter":"Q1 2025","revenue":81000000000,"net_income":19500000000,"ebitda":29000000000}}
  ],
  "sources": ["https://...", "https://..."]
}}
=== END ===

VALIDATION CHECKLIST (perform before returning)
- If no quarterly data is available at all, set "quarters": [] and "quarterly_financials": {{}} but still output valid JSON.
- Never write "OK" in the JSON block.
- Ensure JSON is valid (parse in your head); quarters use "Q# YYYY"; numbers are integers.
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
- A bullet-style 'Financial Analysis Highlights' section with the exact end marker.
- A valid JSON block between the markers with 'quarterly_financials' and/or 'quarters'.
- Sources included inside the JSON (array of URLs).
""".strip()

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        dependencies=dependencies,
        sources=sources,
    )


