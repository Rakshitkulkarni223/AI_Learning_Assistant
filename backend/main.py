import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.agent import handle_user_query
from services.embeddings import get_collection
from services.llm import aggregate_metrics, reset_metrics
from services.long_term_memory import clear_preferences, get_preferences, store_preference
from services.memory_extractor import extract_preference
from services.rate_limiter import rate_limit
from services.short_term_memory import add_message, get_messages

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
    session_id: str | None = None


class SearchRequest(BaseModel):
    query: str


class MemoryRequest(BaseModel):
    fact: str


@app.get("/health")
def health_check():
    """Return a simple health status."""
    try:
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat")
def chat(request: ChatRequest, _client: str = Depends(rate_limit)):
    """Route the user message through the agent with short-term memory."""
    try:
        user_message = request.message.strip()

        if not user_message:
            return {
                "answer": "Please send a message.",
                "sources": [],
                "session_id": request.session_id or "",
                "metrics": aggregate_metrics([]),
            }

        session_id = request.session_id or str(uuid.uuid4())

        add_message(session_id, "user", user_message)
        history = get_messages(session_id)[:-1]

        reset_metrics()
        result = handle_user_query(user_message, history=history)
        metrics = aggregate_metrics()

        add_message(session_id, "assistant", result["answer"])

        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "session_id": session_id,
            "metrics": metrics,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/search")
def search(request: SearchRequest, _client: str = Depends(rate_limit)):
    """Find the most similar chunks for the user's query."""
    try:
        query = request.query.strip()

        if not query:
            return {"results": []}

        collection = get_collection()
        matches = collection.query(
            query_texts=[query],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

        results = []
        for i, doc in enumerate(matches["documents"][0]):
            results.append(
                {
                    "document": matches["metadatas"][0][i]["source"],
                    "text": doc,
                    "score": matches["distances"][0][i],
                }
            )

        return {"results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/memory")
def store_memory(request: MemoryRequest, _client: str = Depends(rate_limit)):
    """Extract and store a user preference from natural language."""
    try:
        fact = request.fact.strip()
        if not fact:
            raise HTTPException(status_code=400, detail="Fact cannot be empty")

        key, value = extract_preference(fact)
        store_preference(key, value)

        return {"status": "ok", "key": key, "value": value}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/memory")
def read_memory():
    """Return all stored user preferences."""
    try:
        return {"preferences": get_preferences()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/memory")
def delete_memory():
    """Clear all stored user preferences."""
    try:
        clear_preferences()
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
