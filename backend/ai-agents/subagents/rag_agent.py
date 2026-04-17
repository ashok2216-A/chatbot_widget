import sys
import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Load sibling files
sys.path.append(os.path.dirname(__file__))
from tool import rag_tool
from rag_prompt import RAG_INSTRUCTION

# Define the Portfolio Search Agent
rag_agent = Agent(
    name="PortfolioSearchAgent",
    model=LiteLlm(model="openrouter/google/gemini-2.5-flash-free"),
    description="I handle queries regarding professional background, skills, projects, and technical abilities found in the knowledge base.",
    tools=[rag_tool],
    instruction=RAG_INSTRUCTION
)
