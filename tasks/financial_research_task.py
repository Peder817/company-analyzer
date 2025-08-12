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
        f"Collect the most recent and accurate financial data available for {company_name}, "
        f"Extract key financial metrics from the latest quarterly or annual financial report of the company. "
        f"Also retrieve relevant historical financial data from the past 1-2 years for comparison,"
        f"including but not limited to revenue, profit/loss, EBITDA, cash flow, debt levels, "
        f"market capitalization, stock performance, and analyst/management comments on performance."
    )

    dep_outputs = ""
    if dependencies:
        dep_outputs = "\n\n".join(
            f"Dependency output from {getattr(dep.agent, 'role', 'previous task')}:\n{getattr(dep, 'output', '')}"
            for dep in dependencies
        )
        description += (
            "\n\nUse the following prior research as a reference to guide your data collection:\n"
            f"{dep_outputs}"
        )

    expected_output = (
        f"A comprehensive and fact-based financial data summary containing {company_name}'s latest financial metrics, "
        f"with clear labels and source references. You pay attention to trends and changes over time."
    )

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        dependencies=dependencies,
    )
