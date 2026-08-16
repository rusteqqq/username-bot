from pathlib import Path
import threading

ARCHIVE_FILE = Path("free_usernames.txt")
_lock = threading.Lock()

def load_free():
    if not ARCHIVE_FILE.exists():
        return []

    result = []
    seen = set()
    with ARCHIVE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            username = line.strip().lower().lstrip("@")
            if username and username not in seen:
                seen.add(username)
                result.append(username)
    return result

def add_free(username):
    username = username.lower().lstrip("@")
    with _lock:
        current = set(load_free())
        if username in current:
            return
        with ARCHIVE_FILE.open("a", encoding="utf-8") as f:
            f.write(username + "\n")
