from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    """Return a hardcoded chat response for Phase 1."""
    try:
        user_message = request.message.strip()

        if not user_message:
            return {"answer": "Please send a message."}

        lower_message = user_message.lower()

        if lower_message == "hello":
            return {"answer": "Hello! I'm your AI Learning Assistant."}

        return {"answer": f"You said: {user_message}"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
