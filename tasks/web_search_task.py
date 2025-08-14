from datetime import datetime
from crewai import Task
from crewai import Agent


def get_latest_quarter():
    now = datetime.utcnow()
    year = now.year
    month = now.month

    if month <= 3:
        quarter = "Q4"
        year -= 1
    elif month <= 6:
        quarter = "Q1"
    elif month <= 9:
        quarter = "Q2"
    else:
        quarter = "Q3"

    return f"{quarter} {year}"


def create_web_search_task(
    agent: Agent,
    company_name: str,
    dependencies: list | None = None,
    sources: list | None = None,
):
    if dependencies is None:
        dependencies = []
    if sources is None:
        sources = []

    latest_quarter = get_latest_quarter()

    description = (
        f"Conduct thorough online research to gather the most recent and relevant information "
        f"about {company_name}, focusing specifically on their financial results for {latest_quarter}. "
        f"Prioritize reliable sources such as official earnings reports, press releases, major news outlets, "
        f"and analyst commentary. Use publication date filters to ensure data is from the past 3 months. "
        f"Extract distinct, fact-based insights that can inform financial and business analysis."
    )

    expected_output = (
        f"A list of at least 5 distinct and verifiable insights about {company_name}'s performance in {latest_quarter}, "
        f"each with a source reference (URL) and publication date."
    )

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        dependencies=dependencies,
        sources=sources,
    )
