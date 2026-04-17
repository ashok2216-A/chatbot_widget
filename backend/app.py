from fastapi import FastAPI, Request
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
# Clean up any accidental quotes or spaces from the env string
ALLOWED_ORIGINS_LIST = [o.strip().replace('"', '').replace("'", "") for o in ALLOWED_ORIGINS_STR.split(",") if o.strip()]

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
    Parses a string for ```a2ui { ... } ``` blocks and returns a list of chunks.
    Chunks are of type "text" or "a2ui".
    """
    # Matches ```a2ui, ```json, or unlabeled blocks containing a JSON object { ... }
    # Matches anything between triple-backticks. We'll handle the JSON parsing inside.
    pattern = r'```(?:[\w\-]*)\s*(\{[\s\S]*?\})\s*```'
    
    chunks = []
    last_pos = 0
    
    # 1. First, find all explicit markdown blocks
    for match in re.finditer(pattern, text):
        start, end = match.span()
        if start > last_pos:
            raw_text = text[last_pos:start]
            if raw_text.strip(): chunks.append({"type": "text", "content": raw_text})
        
        json_content = match.group(1).strip()
        try:
            chunks.append({"type": "a2ui", "content": json.loads(json_content)})
        except Exception:
            chunks.append({"type": "text", "content": match.group(0)})
        last_pos = end
    
    # 2. For the remaining text, try to find "naked" JSON objects containing data_view
    remaining_text = text[last_pos:]
    if "data_view" in remaining_text:
        # Robust search for the first '{' and last '}' containing 'data_view'
        start_idx = remaining_text.find('{')
        end_idx = remaining_text.rfind('}')
        if start_idx != -1 and end_idx > start_idx:
            potential_json = remaining_text[start_idx:end_idx+1]
            try:
                content = json.loads(potential_json)
                pre_text = remaining_text[:start_idx]
                if pre_text.strip(): chunks.append({"type": "text", "content": pre_text})
                chunks.append({"type": "a2ui", "content": content})
                # Check for any remaining text after the JSON block
                remaining_text = remaining_text[end_idx+1:]
            except Exception:
                pass
    
    # 3. Final cleanup of remaining text
    if remaining_text.strip():
        chunks.append({"type": "text", "content": remaining_text})
            
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
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_answer = event.content.parts[0].text
                break

        # ── Global A2UI Hybrid Parsing ────────────────────────────────────────
        logger.info(f"RAW AGENT RESPONSE: {final_answer}")
        chunks = parse_a2ui_chunks(final_answer)
        
        # For backward compatibility and the main "text" reply, we use the original text
        # but the frontend will rely primarily on 'chunks'.
        
        logger.info(f"Successfully generated response for session: {req.session_id}")
        return {
            "reply": final_answer, 
            "chunks": chunks if chunks else [{"type": "text", "content": final_answer}]
        }

    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}", exc_info=True)
        return {"error": str(e)}
