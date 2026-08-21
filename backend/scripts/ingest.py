import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = Path(__file__).parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR.parent / "chroma"

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("OPENAI_API_KEY", "ollama")


def load_documents():
    """Load all .txt files from the documents directory."""
    documents = []
    try:
        for path in sorted(DOCUMENTS_DIR.glob("*.txt")):
            try:
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    documents.append({"source": path.name, "text": text})
            except Exception as exc:
                print(f"Warning: could not read {path}: {exc}")
        return documents
    except Exception as exc:
        print(f"Error loading documents: {exc}")
        return []


def chunk_documents(documents):
    """Split each document into overlapping chunks."""
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )

        chunks = []
        for doc in documents:
            try:
                for chunk in splitter.split_text(doc["text"]):
                    chunks.append({"source": doc["source"], "text": chunk})
            except Exception as exc:
                print(f"Warning: could not chunk {doc['source']}: {exc}")

        return chunks
    except Exception as exc:
        print(f"Error chunking documents: {exc}")
        return []


def store_chunks(chunks):
    """Generate embeddings and store the chunks in ChromaDB."""
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))

        # Wipe old data so a new chunk size creates a fresh collection.
        try:
            client.delete_collection("knowledge")
        except Exception:
            pass

        embedding_function = OpenAIEmbeddingFunction(
            api_key=OLLAMA_API_KEY,
            api_base=OLLAMA_BASE_URL,
            model_name=EMBEDDING_MODEL,
        )

        collection = client.get_or_create_collection(
            name="knowledge",
            embedding_function=embedding_function,
        )

        ids = [f"chunk_{i}" for i in range(len(chunks))]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [{"source": chunk["source"]} for chunk in chunks]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(chunks)
    except Exception as exc:
        print(f"Error storing chunks: {exc}")
        return 0


def main():
    try:
        print(f"Using CHUNK_SIZE={CHUNK_SIZE}, CHUNK_OVERLAP={CHUNK_OVERLAP}")

        documents = load_documents()
        print(f"Documents loaded: {len(documents)}")

        chunks = chunk_documents(documents)
        print(f"Chunks created: {len(chunks)}")

        stored = store_chunks(chunks)
        print(f"Embeddings stored: {stored}")

        if not documents or not chunks or stored == 0:
            sys.exit(1)
    except Exception as exc:
        print(f"Ingestion failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
