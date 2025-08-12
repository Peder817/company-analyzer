from crewai import Crew
from langchain_openai import OpenAI
from dotenv import load_dotenv
import os

from agents.agents.web_search_agent import create_web_search_agent
from agents.agents.financial_research_agent import create_financial_research_agent
from agents.agents.financial_analysis_agent import create_financial_analysis_agent
from agents.agents.report_agent import create_report_agent

from tasks.web_search_task import create_web_search_task
from tasks.financial_research_task import create_financial_research_task
from tasks.financial_analysis_task import create_financial_analysis_task
from tasks.reporting_task import create_reporting_task

from tools import create_search_tool

load_dotenv()

# Ensure API key is present to avoid confusing runtime errors
if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError(
        "Missing OPENAI_API_KEY. Create a .env file with OPENAI_API_KEY=your_key or set the environment variable."
    )

if not os.getenv("SERPAPI_API_KEY"):
    print("Warning: SERPAPI_API_KEY not set. The app will fall back to DuckDuckGo for search.")

llm = OpenAI(
    temperature=0.7,
    model="gpt-4o-mini"
)

search_tool = create_search_tool(os.getenv("SERPAPI_API_KEY"))

# Set the company to analyze
company_name = "Tesla"

# Create agents with search tools
web_search_agent = create_web_search_agent(llm, tools=[search_tool])
financial_research_agent = create_financial_research_agent(llm, tools=[search_tool])
financial_analysis_agent = create_financial_analysis_agent(llm, tools=[search_tool])
report_agent = create_report_agent(llm)

web_search_task = create_web_search_task(web_search_agent, company_name)
financial_research_task = create_financial_research_task(
    financial_research_agent,
    company_name,
    dependencies=[web_search_task]
)
financial_analysis_task = create_financial_analysis_task(
    financial_analysis_agent,
    company_name,
    dependencies=[web_search_task, financial_research_task]
)

sources = []
for task in [web_search_task, financial_research_task]:
    if hasattr(task, "sources") and task.sources:
        sources.extend(task.sources)

reporting_task = create_reporting_task(
    report_agent,
    company_name,
    dependencies=[financial_analysis_task],
    sources=sources,
)

crew = Crew(
    agents=[
        web_search_agent,
        financial_research_agent,
        financial_analysis_agent,
        report_agent
    ],
    tasks=[
        web_search_task,
        financial_research_task,
        financial_analysis_task,
        reporting_task
    ],
    verbose=True
)

if __name__ == "__main__":
    try:
        print(f"Starting company analysis for: {company_name}")
        result = crew.kickoff()
        print("\n--- Final Report ---")
        print(result)
    except Exception as e:
        print(f"An error occurred during execution: {e}")
