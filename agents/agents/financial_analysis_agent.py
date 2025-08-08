from crewai import Agent
from langchain_openai import OpenAI

def create_financial_analysis_agent(llm: OpenAI):
    return Agent(
        role="Senior Financial Analyst",
        goal="Analyze financial data to highlight key figures, draw insights about the company's performance and summarize keytrends",
        backstory=(
            "You are a professional financial analyst with deep knowledge of markets, company reports,"
            " and the ability to interpret key financial indicators. You are great at summarizing and"
            " presenting financial data in a clear and concise manner."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
