from fastapi import FastAPI
from pydantic import BaseModel
from agent import agent

app = FastAPI()

class Query(BaseModel):
    question: str

@app.post("/chat")
async def chat(q: Query):
    response = agent.run(q.question)
    return {"answer": response}
