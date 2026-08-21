import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from services.embeddings import get_collection

EVALUATION_FILE = Path(__file__).parent.parent / "evaluation.json"


def load_evaluation():
    """Load the question/answer pairs used for retrieval evaluation."""
    try:
        with open(EVALUATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"Error loading evaluation file: {exc}")
        return []


def evaluate():
    """Calculate Recall@1, Recall@3, and Recall@5."""
    try:
        collection = get_collection()
        questions = load_evaluation()

        if not questions:
            print("No evaluation questions found.")
            return

        hits_at_1 = 0
        hits_at_3 = 0
        hits_at_5 = 0
        total = len(questions)

        for item in questions:
            try:
                question = item["question"]
                expected = item["expected_document"]

                results = collection.query(
                    query_texts=[question],
                    n_results=5,
                    include=["metadatas"],
                )

                sources = [meta["source"] for meta in results["metadatas"][0]]

                if expected in sources[:1]:
                    hits_at_1 += 1
                if expected in sources[:3]:
                    hits_at_3 += 1
                if expected in sources[:5]:
                    hits_at_5 += 1
            except Exception as exc:
                print(f"Error evaluating question {item}: {exc}")

        print(f"Total questions: {total}")
        print(f"Recall@1: {hits_at_1 / total:.2f}")
        print(f"Recall@3: {hits_at_3 / total:.2f}")
        print(f"Recall@5: {hits_at_5 / total:.2f}")
    except Exception as exc:
        print(f"Evaluation failed: {exc}")


if __name__ == "__main__":
    evaluate()
