from fastapi import APIRouter, HTTPException
import json
from google.genai import types
from schemas.chat import ChatRequest
from core.agent import runner, session_service
from utils.a2ui import parse_a2ui_chunks
from logger import get_logger

logger = get_logger("API_Gateway")
router = APIRouter()

@router.post("/chat")
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
