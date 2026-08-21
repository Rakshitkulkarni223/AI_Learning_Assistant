import time
from collections import deque
from datetime import datetime, timezone

MAX_LOG_SIZE = 1000

_logs = deque(maxlen=MAX_LOG_SIZE)


def record_request(
    request_id: str,
    question: str,
    retrieval_time: float,
    llm_time: float,
    total_time: float,
    tokens: int,
    status: str,
) -> None:
    """Append one request record to the in-memory log."""
    try:
        _logs.append(
            {
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "question": question,
                "retrieval_time": retrieval_time,
                "llm_time": llm_time,
                "total_time": total_time,
                "tokens": tokens,
                "status": status,
            }
        )
    except Exception as exc:
        print(f"Failed to record observability data: {exc}")


def get_stats() -> dict:
    """Return summary statistics and a few recent requests."""
    try:
        if not _logs:
            return {
                "total_requests": 0,
                "failed_requests": 0,
                "average_latency_ms": 0.0,
                "average_retrieval_time_ms": 0.0,
                "average_llm_time_ms": 0.0,
                "total_tokens": 0,
                "recent": [],
            }

        total = len(_logs)
        failed = sum(1 for r in _logs if r["status"] != "success")

        return {
            "total_requests": total,
            "failed_requests": failed,
            "average_latency_ms": round(
                sum(r["total_time"] for r in _logs) / total, 2
            ),
            "average_retrieval_time_ms": round(
                sum(r["retrieval_time"] for r in _logs) / total, 2
            ),
            "average_llm_time_ms": round(
                sum(r["llm_time"] for r in _logs) / total, 2
            ),
            "total_tokens": sum(r["tokens"] for r in _logs),
            "recent": list(_logs)[-5:],
        }
    except Exception as exc:
        print(f"Failed to compute observability stats: {exc}")
        return {
            "total_requests": 0,
            "failed_requests": 0,
            "average_latency_ms": 0.0,
            "average_retrieval_time_ms": 0.0,
            "average_llm_time_ms": 0.0,
            "total_tokens": 0,
            "recent": [],
        }
