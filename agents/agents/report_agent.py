from crewai import Agent
from langchain_openai import OpenAI
from langchain.tools.base import BaseTool


def create_report_agent(llm: OpenAI, tools: list | None = None) -> Agent:
    tools = [t for t in (tools or []) if isinstance(t, BaseTool) or hasattr(t, "name")]
    return Agent(
        role="Financial Report Writer",
        goal=(
            "Summarize all findings into a concise and informative report about the company´s financial performance."
            "Compose a clear, concise company report including an executive summary, "
            "a section focused on the latest financial results, and a separate section "
            "highlighting key trends and comparisons with past years. Make sure to Include key facts and figures."
        ),
        backstory=(
            "You are a professional business skilled in summarizing complex financial data "
            "into accessible insights for business stakeholders, packaged into easy-to-understand business reports. "
            "You are fact based and great at summarizing and presenting financial data and business insights in a clear and concise manner."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools,
    )
