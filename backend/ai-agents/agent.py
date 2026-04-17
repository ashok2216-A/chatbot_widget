import sys
import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# ── Coordinator prompt ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from root_prompt import ROOT_INSTRUCTION  # type: ignore

# ── Subagents (one package per agent) ─────────────────────────────────────────
# Each subfolder is a Python package with its own agent.py / tools.py / prompt.py
_subagents_dir = os.path.join(os.path.dirname(__file__), "subagents")
sys.path.insert(0, _subagents_dir)

from rag.agent import rag_agent           # type: ignore
from email.agent import email_agent       # type: ignore
from scheduler.agent import scheduler_agent  # type: ignore

# ── Root Coordinator Agent ─────────────────────────────────────────────────────
root_agent = LlmAgent(
    name="CoordinatorAgent",
    model=LiteLlm(
        model="openrouter/google/gemini-2.0-flash-001",
        fallbacks=["groq/llama-3.3-70b-versatile", "mistral/mistral-large-latest"],
    ),
    description=(
        "Central coordinator. Routes portfolio queries to PortfolioSearchAgent, "
        "email tasks to EmailAgent, and calendar tasks to SchedulerAgent."
    ),
    instruction=ROOT_INSTRUCTION,
    sub_agents=[
        rag_agent,
        email_agent,
        scheduler_agent,
    ],
)
