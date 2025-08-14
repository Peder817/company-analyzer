import re
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

    # Plocka ihop output från dependencies
    dependency_texts_parts = []
    for dep in dependencies:
        if hasattr(dep, 'output'):
            text = getattr(dep, 'output', None)
            if text:
                dependency_texts_parts.append(str(text))
    dependency_texts = "\n\n".join(dependency_texts_parts)

    # Försök hitta senaste kvartalet i dependency-texten
    latest_quarter = None
    quarter_pattern = re.compile(r"Q[1-4]\s20\d{2}")
    match = quarter_pattern.search(dependency_texts)
    if match:
        latest_quarter = match.group(0)
    else:
        latest_quarter = "the most recent quarter"

    description = (
        f"Analyze the financial data for {company_name} from {latest_quarter} and provide a comprehensive analysis.\n\n"
        f"Available data:\n{dependency_texts}\n\n"
        f"REQUIRED: Provide at least 5-7 specific financial highlights using bullet points. Include:\n"
        f"• Revenue figures and growth rates\n"
        f"• Profitability metrics (margins)\n"
        f"• Key financial ratios\n"
        f"• Cash flow indicators\n"
        f"• Growth trends\n\n"
        f"If data is missing, use web search to find current financial information. "
        f"Always provide specific numbers and percentages when available."
    )

    expected_output = (
        f"A detailed financial analysis of {company_name} with 5-7 bullet points covering:\n"
        f"• Revenue performance and growth\n"
        f"• Profitability metrics\n"
        f"• Key financial ratios\n"
        f"• Cash flow analysis\n"
        f"• Growth trends\n"
        f"Each point must include specific numbers, percentages, or data. Use bullet points (•) for formatting."
    )

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
        dependencies=dependencies,
        sources=sources
    )

