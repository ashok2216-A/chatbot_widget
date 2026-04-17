import os
import sys
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# Ensure python understands where the root backend folder is
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.append(_BACKEND_DIR)

# Add ai-agents to path
_AGENTS_DIR = os.path.join(_BACKEND_DIR, 'ai-agents')
if _AGENTS_DIR not in sys.path:
    sys.path.append(_AGENTS_DIR)

from agent import root_agent  # type: ignore

# Singletons for the application
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="portfolio_chatbot",
    session_service=session_service
)
