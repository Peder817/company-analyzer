from crewai import Agent, Task, Crew
from langchain_openai import OpenAI
from dotenv import load_dotenv
import os

from langchain_community.utilities.serpapi import SerpAPIWrapper
from langchain.tools import Tool

load_dotenv()

llm = OpenAI(temperature=0.7)

# Skapa en testagent
analyst = Agent(
    role='Financial Analyst',
    goal='Analyze the company named in the taskand deliver insights',
    backstory='You are a financial analyst that analyzes financial reports and market trends.',
    verbose=True,
    llm=llm
)

# Skapa en testuppgift
task = Task(
    description='Analyze the financial performancecompany Tesla and deliver insights',
    agent=analyst,
    expected_output='An analysis with three key insights about the company'
)

# Skapa crew
crew = Crew(
    agents=[analyst],
    tasks=[task],
    verbose=True
)

# Kör crew
crew.kickoff()