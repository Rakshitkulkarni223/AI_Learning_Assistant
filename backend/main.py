from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.llm import call_llm

app = FastAPI(title="AI Learning Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health_check():
    """Return a simple health status."""
    try:
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat")
def chat(request: ChatRequest):
    """Send the user message to the LLM and return the generated answer."""
    try:
        user_message = request.message.strip()

        if not user_message:
            return {"answer": "Please send a message."}

        answer = call_llm(user_message)
        return {"answer": answer}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
