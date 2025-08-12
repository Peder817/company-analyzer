from crewai import Task
from crewai import Agent


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

    description = (
        f"Conduct thorough online research to gather recent and relevant information "
        f"about {company_name}. Focus on reliable sources such as news articles, press releases, "
        f"media mentions, and analyst commentary. Extract distinct, fact-based insights "
        f"that can inform financial and business analysis."
    )
    expected_output = (
        f"A list of at least 5 distinct and verifiable insights about {company_name}, "
        f"each with a source reference and publication date."
    )

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        dependencies=dependencies,
    )
