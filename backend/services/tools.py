from services.rag import answer_with_rag

AVAILABLE_COURSES = [
    "React",
    "TypeScript",
    "Java",
    "AWS",
    "Docker",
    "Kubernetes",
    "AI",
]


def search_knowledge(query: str) -> dict:
    """Answer a study question using the RAG knowledge base."""
    return answer_with_rag(query)


def search_courses(query: str = "") -> dict:
    """Return available courses, optionally filtered by a keyword."""
    try:
        keyword = query.strip().lower()
        if keyword:
            matches = [
                c for c in AVAILABLE_COURSES if keyword in c.lower()
            ]
            if matches:
                answer = "Available courses:\n" + "\n".join(
                    f"- {c}" for c in matches
                )
            else:
                all_courses = "\n".join(f"- {c}" for c in AVAILABLE_COURSES)
                answer = f"No courses match '{query}'.\nAll available courses:\n{all_courses}"
        else:
            all_courses = "\n".join(f"- {c}" for c in AVAILABLE_COURSES)
            answer = "Available courses:\n" + all_courses

        return {"answer": answer, "sources": []}
    except Exception as exc:
        return {"answer": f"Course search error: {exc}", "sources": []}


def get_user_courses() -> dict:
    """Return the courses the user is currently enrolled in."""
    try:
        return {
            "answer": "Your enrolled courses:\n- React\n- TypeScript\n- Docker",
            "sources": [],
        }
    except Exception as exc:
        return {"answer": f"User courses error: {exc}", "sources": []}
