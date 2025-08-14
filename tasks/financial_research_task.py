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

    description = (
        f"Step 1: Use the 'financial_data' tool to retrieve structured, numerical financial data for {company_name} "
        f"covering the latest quarterly or annual report plus 1–2 years of history. "
        f"Include revenue, profit/loss, EBITDA, cash flow, debt levels, market capitalization, and stock performance.\n"
        f"Step 2: Use the 'web_search' tool to find analyst commentary, management statements, and recent news "
        f"that provide context to the financial data.\n"
        f"Step 3: Compile all findings into a structured output, clearly labeling each metric and attaching source references."
    )

    if dependencies:
        dep_outputs = "\n\n".join(
            f"Dependency output from {getattr(dep.agent, 'role', 'previous task')}:\n{getattr(dep, 'output', '')}"
            for dep in dependencies
        )
        description += (
            "\n\nUse the following prior research as reference material when interpreting the data:\n"
            f"{dep_outputs}"
        )

    expected_output = (
        f"A comprehensive financial data summary for {company_name}, "
        f"including the latest figures, historical comparison, and qualitative insights from credible sources. "
        f"All data points should have clear labels and sources."
    )

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        dependencies=dependencies,
        sources=sources
    )

