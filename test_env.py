from dotenv import load_dotenv
import os

load_dotenv()

print("OPENAI key:", os.getenv("OPENAI_API_KEY"))
print("SERPER key:", os.getenv("SERPER_API_KEY"))
