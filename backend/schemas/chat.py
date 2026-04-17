from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str  # Frontend supplies this per page-load
