from crewai import Agent
from langchain_openai import OpenAI
from langchain.tools.base import BaseTool


def create_financial_research_agent(llm: OpenAI, tools: list | None = None) -> Agent:
    tools = [t for t in (tools or []) if isinstance(t, BaseTool) or hasattr(t, "name")]
    return Agent(
        role="Financial Data Collector",
        goal=(
            "Gather accurate and up-to-date financial data for the given company including the most recent quarterly or annual financial report"
            "Research credible public sources, such as stock exchanges, company filings and trusted financial news outlets."
            "Also gather the key comments on performance from financial analysts or company management."
        ),
        backstory=(
            "You are an expert in sourcing company financial data from reliable sources. "
            "Your mission is to ensure that the dataset you compile is complete, accurate, "
            "and ready for deeper financial analysis."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools,
    )
