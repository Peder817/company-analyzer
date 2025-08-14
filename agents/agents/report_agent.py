from crewai import Agent
from langchain_openai import OpenAI
from langchain.tools.base import BaseTool


def create_report_agent(llm: OpenAI, tools: list | None = None) -> Agent:
    tools = [t for t in (tools or []) if isinstance(t, BaseTool) or hasattr(t, "name")]
    return Agent(
        role="Financial Report Writer",
        goal=(
            "Create a concise but complete business report by following the structure exactly. "
            "Write each section concisely but completely before moving to the next. "
            "Focus on essential information without unnecessary detail. Always include the end marker. "
            "For financial sections, use simple formatting and avoid complex symbols or formatting."
        ),
        backstory=(
            "You are a skilled business analyst who writes concise, complete reports. "
            "You focus on essential information without unnecessary detail. "
            "You always complete what you start and include required markers. "
            "You use simple, clean formatting and avoid complex symbols or formatting that could cause issues."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools,
    )
