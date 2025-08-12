from crewai import Task
from crewai import Agent


def create_reporting_task(
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
        f"Compile the findings from the research and financial analysis of {company_name} "
        f"into a well-structured, business-friendly report. The report should synthesize "
        f"key insights, financial performance, and strategic recommendations. "
        f"Include a 'Sources' section listing all main references, URLs, and data points used."
    )
    expected_output = (
        f"A professional business report for {company_name} that includes: "
        f"(1) Executive summary, (2) Key research insights, "
        f"(3) Financial analysis highlights, (4) Recommendations, and (5) Sources."
    )

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        dependencies=dependencies,
    )

