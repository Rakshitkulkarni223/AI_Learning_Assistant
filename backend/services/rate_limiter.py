import os
import time
from threading import Lock

from dotenv import load_dotenv
from fastapi import HTTPException, Request, status

load_dotenv()

MAX_REQUESTS = int(os.getenv("RATE_LIMIT", "10"))
WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW", "60"))


class RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self):
        self._history = {}
        self._lock = Lock()

    def __call__(self, request: Request) -> str:
        try:
            client = request.client.host if request.client else "unknown"
            now = time.time()

            with self._lock:
                timestamps = self._history.get(client, [])
                self._history[client] = [
                    t for t in timestamps if now - t < WINDOW_SECONDS
                ]

                if len(self._history[client]) >= MAX_REQUESTS:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please try again.",
                    )

                self._history[client].append(now)

            return client
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rate limiter error: {exc}",
            )


rate_limit = RateLimiter()
