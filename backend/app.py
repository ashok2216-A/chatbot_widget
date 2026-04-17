from fastapi import FastAPI, Request
import warnings
# Suppress ADK experimental feature warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*PLUGGABLE_AUTH is enabled.*")

import litellm
# Suppress LiteLLM "Provider List" logs
litellm.suppress_debug_info = True

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import sys
import json
import re

# ALWAYS load env first before initializing API clients in other scripts
load_dotenv()

# Make sure python understands where the root backend folder is
sys.path.append(os.path.dirname(__file__))
from logger import get_logger

logger = get_logger("API_Gateway")

# Add new ADK root agent to path so we can import the agent
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))
from agent import root_agent  # type: ignore

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Setup ADK asynchronous execution orchestration
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="portfolio_chatbot",
    session_service=session_service
)

app = FastAPI()

ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8000")

# Bulletproof Origin Parsing: Extract only the base (scheme + host) from any URL provided
from urllib.parse import urlparse
ALLOWED_ORIGINS_LIST = []
for o in ALLOWED_ORIGINS_STR.split(","):
    clean = o.strip().replace('"', '').replace("'", "").replace("[", "").replace("]", "")
    if clean:
        parsed = urlparse(clean)
        # Reconstruct base origin: scheme://netloc (e.g. https://ashok2216-a.github.io)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"
        if base_origin != "://":
            ALLOWED_ORIGINS_LIST.append(base_origin)

# Ensure internal health check is always allowed via localhost/render internal access
# (Optional but recommended for stability)
logger.info(f"HARDENED ALLOWED ORIGINS: {ALLOWED_ORIGINS_LIST}")

# ── CORS must be added FIRST so preflight OPTIONS responses work correctly ──
# The CORSMiddleware wraps everything: it handles OPTIONS itself and injects
# Access-Control-Allow-Origin on all responses from allowed origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS_LIST,
    allow_methods=["OPTIONS", "POST", "GET"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ── Strict Origin validation ──────────────────────────────────────────────────
# Runs INSIDE the CORS wrapper. We skip OPTIONS (already handled by CORS above)
# and the /health route. Everything else must carry a recognised Origin header.
@app.middleware("http")
async def strict_origin_middleware(request: Request, call_next):
    # Always pass through OPTIONS preflight and health checks BEFORE any logic
    if request.method == "OPTIONS" or request.url.path == "/health":
        return await call_next(request)

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    is_valid_origin = origin and any(origin.rstrip('/') == a.rstrip('/') for a in ALLOWED_ORIGINS_LIST)
    is_valid_referer = referer and any(referer.rstrip('/') == a.rstrip('/') for a in ALLOWED_ORIGINS_LIST)
    is_allowed = is_valid_origin or is_valid_referer

    if not is_allowed:
        logger.warning(f"Blocked request from origin={origin} referer={referer}")
        return JSONResponse(
            status_code=403,
            content={"detail": "Access Denied"}
        )

    return await call_next(request)

# ─── A2UI Parser Helper ───────────────────────────────────────────────────────

def parse_a2ui_chunks(text: str):
    """
    Enhanced parser for A2UI Hybrid Protocol.
    Splits text into chunks of 'text' and 'a2ui' (JSON blocks).
    Handles malformed JSON and trailing commas gracefully.
    """
    if not text: return []
    chunks = []
    # Match triple backtick JSON blocks
    pattern = r'```(?:[\w\-]*)\s*(\{[\s\S]*?\})\s*```'
    last_pos = 0

    def clean_json(s: str) -> str:
        # Remove trailing commas in arrays/objects before parsing
        s = re.sub(r",\s*([\]\}])", r"\1", s)
        return s

    for match in re.finditer(pattern, text):
        start, end = match.span()
        # Add preceding text
        if start > last_pos:
            pre_text = text[last_pos:start].strip()
            if pre_text: chunks.append({"type": "text", "content": pre_text})
        
        json_str = clean_json(match.group(1).strip())
        try:
            chunks.append({"type": "a2ui", "content": json.loads(json_str)})
        except Exception:
            # If JSON parsing fails, treat it as raw text
            chunks.append({"type": "text", "content": match.group(0)})
        last_pos = end
    
    # Check for any remaining text after the last block
    remaining = text[last_pos:].strip()
    if remaining:
        # Fallback for "naked" data_view blocks without backticks
        if "data_view" in remaining:
            try:
                # Basic search for the first { and last }
                start_idx = remaining.find('{')
                end_idx = remaining.rfind('}')
                if start_idx != -1 and end_idx > start_idx:
                    json_str = clean_json(remaining[start_idx:end_idx+1])
                    content = json.loads(json_str)
                    pre = remaining[:start_idx].strip()
                    if pre: chunks.append({"type": "text", "content": pre})
                    chunks.append({"type": "a2ui", "content": content})
                    remaining = remaining[end_idx+1:].strip()
            except Exception:
                pass
        
        if remaining:
            chunks.append({"type": "text", "content": remaining})
            
    return chunks

# ─────────────────────────────────────────────────────────────────────────────

# Health check to keep Render awake
@app.get("/health")
def health_check():
    logger.debug("Health check ping received.")
    return {"status": "alive"}

# Request schema
class ChatRequest(BaseModel):
    message: str
    session_id: str  # Frontend supplies this per page-load

# Chat endpoint with A2UI JSON support
@app.post("/chat")
async def chat(req: ChatRequest):
    logger.info(f"Received chat request for session: {req.session_id}")
    try:
        # Reuse existing ADK session or create a new one
        try:
            session = await session_service.get_session(
                app_name="portfolio_chatbot",
                user_id="web_user",
                session_id=req.session_id
            )
        except Exception:
            session = None

        if not session:
            session = await session_service.create_session(
                app_name="portfolio_chatbot",
                user_id="web_user",
                session_id=req.session_id
            )

        content = types.Content(role='user', parts=[types.Part(text=req.message)])
        final_answer = "I couldn't process your request."

        async for event in runner.run_async(
            user_id="web_user",
            session_id=req.session_id,
            new_message=content
        ):
            # ── Informational Logging (No message content) ────────────────────
            if event.author:
                 logger.info(f"→ Agent '{event.author}' started processing...")
            
            # Log tool calls using the correct helper method
            calls = event.get_function_calls()
            if calls:
                for call in calls:
                    logger.info(f"  [Tool Call] {call.name} with args: {json.dumps(call.args)}")

            if event.is_final_response():
                if event.content and event.content.parts:
                    final_answer = event.content.parts[0].text
                break

        # ── Global A2UI Hybrid Parsing ────────────────────────────────────────
        chunks = parse_a2ui_chunks(final_answer)
        
        logger.info(
            f"Successfully generated response for session: {req.session_id} | "
            f"Size: {len(final_answer)} chars | Chunks: {len(chunks)}"
        )
        return {
            "reply": final_answer, 
            "chunks": chunks if chunks else [{"type": "text", "content": final_answer}]
        }

    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}", exc_info=True)
        return {"error": str(e)}
