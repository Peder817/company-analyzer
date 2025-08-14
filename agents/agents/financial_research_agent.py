from datetime import datetime
from crewai import Agent
from langchain_openai import OpenAI
from langchain.tools.base import BaseTool


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


def create_financial_research_agent(llm: OpenAI, tools: list | None = None) -> Agent:
    tools = [t for t in (tools or []) if isinstance(t, BaseTool) or hasattr(t, "name")]

    latest_quarter = get_latest_quarter()

    return Agent(
        role="Financial Data Collector",
        goal=(
            f"1. Use the 'financial_data' tool first to retrieve the company's latest structured "
            f"financial data for {latest_quarter} and the previous 1–2 years, including income statements, "
            f"balance sheets, and cash flow statements.\n"
            f"2. Then, use the 'web_search' tool to find recent news, analyst commentary, and any updates "
            f"related to {latest_quarter} that are not included in the structured data.\n"
            f"3. Compile all findings into a complete dataset for deeper analysis."
        ),
        backstory=(
            "You are an expert in gathering financial data from multiple sources. "
            "Your approach is to always prioritize structured financial data from reliable databases "
            "and then supplement it with qualitative insights from credible news sources, "
            "analyst reports, and official company announcements."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools,
    )

