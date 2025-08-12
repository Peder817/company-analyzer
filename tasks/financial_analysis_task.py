from crewai import Task
from crewai import Agent

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

    dependency_texts_parts = []
    for dep in dependencies:
        if hasattr(dep, 'output'):
            text = getattr(dep, 'output', None)
            if text:
                dependency_texts_parts.append(str(text))
    dependency_texts = "\n\n".join(dependency_texts_parts)

    description = (
        f"You are provided with the following financial research data about {company_name}:\n\n"
        f"{dependency_texts}\n\n"
        f"Analyze this financial data to identify performance, key trends, strengths, weaknesses, "
        f"opportunities, and risks. Consider profitability, liquidity, leverage, growth, and "
        f"market positioning."
    )

    expected_output = (
        f"A concise financial analysis of {company_name} highlighting at least 3 major insights "
        f"and any potential red flags."
    )

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        dependencies=dependencies,
    )
