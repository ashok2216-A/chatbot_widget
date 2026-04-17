import sys
import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Load Local Coordinator Prompt
sys.path.append(os.path.dirname(__file__))
from root_prompt import ROOT_INSTRUCTION  # type: ignore

# Import the RAG Subagent and Tool
sys.path.append(os.path.join(os.path.dirname(__file__), 'subagents'))
from rag_agent import rag_agent  # type: ignore

root_agent = LlmAgent(
    name="CoordinatorAgent",
    model=LiteLlm(model="openrouter/openai/gpt-4o-mini"),
    description="I am the central coordinator. I handle general greetings and route specific portfolio data queries to my subagent.",
    instruction=ROOT_INSTRUCTION,
    sub_agents=[
        rag_agent
    ]
)
