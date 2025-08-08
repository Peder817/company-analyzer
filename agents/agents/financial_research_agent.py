from crewai import Agent
from langchain_openai import OpenAI

def create_financial_data_agent(llm: OpenAI):
    return Agent(
        role="Financial Data Collector",
        goal="Gather key financial figures like revenue, profit, and growth trends from online sources",
        backstory=(
            "You are an expert at finding and extracting accurate financial data about companies from"
            " reports, websites, and articles."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )