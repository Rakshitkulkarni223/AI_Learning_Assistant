from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.embeddings import get_collection
from services.rag import answer_with_rag

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


class SearchRequest(BaseModel):
    query: str


@app.get("/health")
def health_check():
    """Return a simple health status."""
    try:
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat")
def chat(request: ChatRequest):
    """Answer the user's question using RAG."""
    try:
        user_message = request.message.strip()

        if not user_message:
            return {"answer": "Please send a message.", "sources": []}

        return answer_with_rag(user_message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/search")
def search(request: SearchRequest):
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
