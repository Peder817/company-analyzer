from crewai import Agent
from langchain_openai import OpenAI

def create_report_agent(llm: OpenAI):
    return Agent(
        role="Financial Report Writer",
        goal="Summarize all findings into a concise and informative report about the company, capturing the key insights and trends."
        "Include key facts and figures, and provide a clear and concise summary of the company's financial performance.",
        backstory=(
            "You are a professional writer who turns complex data and insights into clear, useful business reports."
            "You are fact based and great at summarizing and presenting financial data and business insights in a clear and concise manner."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
