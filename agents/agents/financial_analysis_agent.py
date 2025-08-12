from crewai import Agent
from langchain_openai import OpenAI
from langchain.tools.base import BaseTool


def create_financial_analysis_agent(llm: OpenAI, tools: list | None = None) -> Agent:
    tools = [t for t in (tools or []) if isinstance(t, BaseTool) or hasattr(t, "name")]
    return Agent(
        role="Senior Financial Analyst",
        goal=(
            "Analyze financial data provided to highlight key figures, and draw insights about the company's performance for the past 1-3 years."
            "Highlight significant trends, improvements or declines, and explain possible reasons."
            "Conduct additional web search if required to deliver an excellent answer."
        ),
        backstory=(
            "You are a professional financial analyst with deep knowledge of markets and company reports, "
            "and the ability to interpret key financial indicators. You will be given prior web search results,"
            "use them to focus on collecting hard financial figures, not rehashing news." 
            "You interpret numbers, spot patterns over time, and provide clear "
            "factful insights on the company’s financial health and performance in a clear and concise manner."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools,
    )
