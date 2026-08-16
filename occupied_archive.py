from pathlib import Path
import threading

ARCHIVE_FILE = Path("occupied_usernames.txt")
_lock = threading.Lock()

def load_occupied():
    if not ARCHIVE_FILE.exists():
        return set()

    with ARCHIVE_FILE.open("r", encoding="utf-8") as f:
        return {
            line.strip().lower().lstrip("@")
            for line in f
            if line.strip()
        }

def add_occupied(username):
    username = username.lower().lstrip("@")

    with _lock:
        current = load_occupied()
        if username in current:
            return

        with ARCHIVE_FILE.open("a", encoding="utf-8") as f:
            f.write(username + "\n")
