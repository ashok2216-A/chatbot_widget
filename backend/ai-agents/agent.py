import sys
import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# ── Coordinator prompt ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from prompt import ROOT_INSTRUCTION  # type: ignore

# ── Subagents (one package per agent) ─────────────────────────────────────────
_subagents_dir = os.path.join(os.path.dirname(__file__), "subagents")
sys.path.insert(0, _subagents_dir)

from rag_agent.agent import rag_agent           # type: ignore
from email_agent.agent import email_agent       # type: ignore
from scheduler_agent.agent import scheduler_agent  # type: ignore

# ── Fallback model list ───────────────────────────────────────────────────────
# Ordered by priority: cheap/fast first, heavier as last resort.
# max_tokens is kept LOW (1500) to avoid OpenRouter 402 credit errors.
MODEL_FALLBACKS = [
    "groq/llama-3.3-70b-versatile",     # Fast, generous free tier
    "groq/gemma2-9b-it",                # Lightweight, separate Groq TPM bucket
    "groq/llama-3.1-8b-instant",        # Very fast, low token usage
    "mistral/mistral-small-latest",     # Separate Mistral rate limit bucket
    "mistral/mistral-large-latest",     # Heavy fallback
]

# ── Root Coordinator Agent ─────────────────────────────────────────────────────
root_agent = LlmAgent(
    name="FRIDAY",
    model=LiteLlm(
        model="openrouter/google/gemini-2.0-flash-001",
        fallbacks=MODEL_FALLBACKS,
        max_tokens=1500,        # Reduced from 4000 — prevents OpenRouter 402
        temperature=0.5,
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
