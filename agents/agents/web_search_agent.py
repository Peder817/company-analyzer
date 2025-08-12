from crewai import Agent
from langchain_openai import OpenAI
from langchain.tools.base import BaseTool


def create_web_search_agent(llm: OpenAI, tools: list | None = None) -> Agent:
    tools = [t for t in (tools or []) if isinstance(t, BaseTool) or hasattr(t, "name")]
    return Agent(
        role="Senior Web Researcher",
        goal=(
            "Find the most relevant and recent information, specifically the latest quarterly or annual financial reports,"
            "about the given company and deliver distinct, fact-based insights from reliable sources such as "
            "news articles, media mentions, and analyst reports."
        ),
        backstory=(
            "You are a skilled business researcher who excels at uncovering valuable insights "
            "about companies using online search tools. You focus on accuracy, recency, "
            "and clarity to provide a solid foundation for further analysis."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools,
    )
