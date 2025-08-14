from crewai import Agent
from langchain_openai import OpenAI
from langchain.tools.base import BaseTool


def create_financial_analysis_agent(llm: OpenAI, tools: list | None = None) -> Agent:
    tools = [t for t in (tools or []) if isinstance(t, BaseTool) or hasattr(t, "name")]
    return Agent(
        role="Senior Financial Analyst",
        goal=(
            "Conduct comprehensive financial analysis by examining revenue, profitability, growth trends, "
            "financial ratios, cash flow, and liquidity metrics. Provide detailed insights with specific numbers, "
            "percentages, and trends. Always support analysis with concrete data points and explain business implications."
        ),
        backstory=(
            "You are a senior financial analyst with 15+ years of experience analyzing Fortune 500 companies. "
            "You excel at interpreting financial statements, calculating key ratios, and identifying trends that "
            "drive business performance. You focus on quantitative analysis and provide actionable insights backed "
            "by data. You always structure your analysis with clear sections and use bullet points for readability."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools,
    )
