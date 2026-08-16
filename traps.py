from database import connection

def add_trap(username, user_id):
    username = username.lower().lstrip("@")

    with connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO traps(username, user_id) VALUES (?, ?)",
            (username, user_id)
        )
        conn.commit()

def get_traps(user_id):
    with connection() as conn:
        return [
            row[0]
            for row in conn.execute(
                "SELECT username FROM traps WHERE user_id=? ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()
        ]
