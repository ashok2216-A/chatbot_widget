from fastapi import FastAPI, Request
import warnings
# Suppress ADK experimental feature warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*PLUGGABLE_AUTH is enabled.*")

import litellm
# Suppress LiteLLM "Provider List" logs
litellm.suppress_debug_info = True

from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import sys

# ALWAYS load env first before initializing API clients in other scripts
load_dotenv()

# Make sure python understands where the root backend folder is
sys.path.append(os.path.dirname(__file__))
from logger import get_logger

logger = get_logger("API_Gateway")

# Import routers and core setup
from routes import chat, health

app = FastAPI()

# ─── Global Error Handling ───────────────────────────────────────────────────

class AgentError(Exception):
    """Custom exception for AI orchestration failures."""
    pass

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"UNHANDLED ERROR: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "reply": "I encountered an internal error. Please try again or check the logs.",
            "error": str(exc)
        }
    )

@app.exception_handler(AgentError)
async def agent_error_handler(request: Request, exc: AgentError):
    logger.warning(f"AGENT ERROR: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"reply": f"The agent failed: {str(exc)}", "error": "agent_failure"}
    )

# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8000")

# Bulletproof Origin Parsing
from urllib.parse import urlparse
ALLOWED_ORIGINS_LIST = []
for o in ALLOWED_ORIGINS_STR.split(","):
    clean = o.strip().replace('"', '').replace("'", "").replace("[", "").replace("]", "")
    if clean:
        parsed = urlparse(clean)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"
        if base_origin != "://":
            ALLOWED_ORIGINS_LIST.append(base_origin)

logger.info(f"HARDENED ALLOWED ORIGINS: {ALLOWED_ORIGINS_LIST}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS_LIST,
    allow_methods=["OPTIONS", "POST", "GET"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.middleware("http")
async def strict_origin_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path == "/health":
        return await call_next(request)

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    is_valid_origin = origin and any(origin.rstrip('/') == a.rstrip('/') for a in ALLOWED_ORIGINS_LIST)
    is_valid_referer = referer and any(referer.rstrip('/') == a.rstrip('/') for a in ALLOWED_ORIGINS_LIST)
    is_allowed = is_valid_origin or is_valid_referer

    if not is_allowed:
        logger.warning(f"Blocked request from origin={origin} referer={referer}")
        return JSONResponse(status_code=403, content={"detail": "Access Denied"})

    return await call_next(request)

# ─── Include Routers ─────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(chat.router)
