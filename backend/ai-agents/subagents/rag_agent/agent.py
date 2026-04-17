from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import RAG_INSTRUCTION  # type: ignore
from .tools import rag_tool          # type: ignore

rag_agent = Agent(
    name="PortfolioSearchAgent",
    model=LiteLlm(
        model="openrouter/google/gemini-2.0-flash-001",
        fallbacks=["groq/llama-3.3-70b-versatile", "mistral/mistral-large-latest"],
    ),
    description=(
        "Handles queries about professional background, skills, projects, "
        "education, and technical abilities found in the knowledge base."
    ),
    tools=[rag_tool],
    instruction=RAG_INSTRUCTION,
)
