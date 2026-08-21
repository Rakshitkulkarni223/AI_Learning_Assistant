import threading

_lock = threading.Lock()
_memory = {}


def add_message(session_id: str, role: str, content: str) -> None:
    """Append a message to the session's short-term memory."""
    try:
        with _lock:
            _memory.setdefault(session_id, [])
            _memory[session_id].append({"role": role, "content": content})
    except Exception as exc:
        print(f"Error adding message to memory: {exc}")


def get_messages(session_id: str) -> list:
    """Return a copy of the session's messages."""
    try:
        with _lock:
            return list(_memory.get(session_id, []))
    except Exception as exc:
        print(f"Error getting messages from memory: {exc}")
        return []


def clear_messages(session_id: str) -> None:
    """Remove a session's messages."""
    try:
        with _lock:
            if session_id in _memory:
                del _memory[session_id]
    except Exception as exc:
        print(f"Error clearing memory: {exc}")
