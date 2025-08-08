from crewai import Agent
from langchain_openai import OpenAI

def create_web_search_agent(llm: OpenAI):
    return Agent(
        role="Senior Web Researcher",
        goal="Find the most relevant and recent information about the given company and deliver distinct  and fact basedinsights"
        "based on news, media mentions, analyst and facts from reliable sources.",
        backstory=(
            "You are a skilled business researcher who knows how to find"
            " the most useful articles, news, and insights about companies using online search tools."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
