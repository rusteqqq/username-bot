import asyncio
from pathlib import Path

from telethon import TelegramClient, errors, functions

from config import SESSION_NAME, CHECK_DELAY
from rating import rate_username
from occupied_archive import load_occupied, add_occupied
from free_archive import load_free, add_free


PURCHASE_FILE = Path("purchase_usernames.txt")


class ScannerCooldown(Exception):
    """Telegram temporarily blocked username checks."""
    def __init__(self, seconds: int):
        self.seconds = int(seconds)
        super().__init__(f"FloodWait: {self.seconds} seconds")


def load_purchase():
    if not PURCHASE_FILE.exists():
        return set()

    with PURCHASE_FILE.open("r", encoding="utf-8") as f:
        return {
            line.strip().lower().lstrip("@")
            for line in f
            if line.strip()
        }


def add_purchase(username):
    username = username.lower().lstrip("@")

    with PURCHASE_FILE.open("a", encoding="utf-8") as f:
        # Не дублируем записи.
        if username not in load_purchase():
            f.write(username + "\n")


async def check_one(client, username):
    username = username.lower().lstrip("@")

    try:
        result = await client(
            functions.account.CheckUsernameRequest(
                username=username
            )
        )
        return "free" if bool(result) else "occupied"

    except errors.UsernameOccupiedError:
        return "occupied"

    except errors.UsernamePurchaseAvailableError:
        return "purchase"

    except errors.UsernameInvalidError:
        return "invalid"

    except errors.FloodWaitError as e:
        # ВАЖНО: больше НЕ ждём здесь десятки часов.
        # Сразу сообщаем боту о cooldown.
        raise ScannerCooldown(e.seconds)

    except Exception as e:
        print(f"⚠️ {type(e).__name__}")
        return "error"


async def find_free_usernames(
    candidates,
    api_id,
    api_hash,
    minimum_rating=0,
    limit=5,
):
    occupied = load_occupied()
    free = set(load_free())
    purchase = load_purchase()

    # Уже проверенные username не трогаем повторно.
    already_checked = occupied | free | purchase

    unique = []
    seen = set()

    for username in candidates:
        username = username.lower().lstrip("@")

        if username in seen or username in already_checked:
            continue

        seen.add(username)
        unique.append(username)

    unique.sort(key=rate_username, reverse=True)

    results = []

    async with TelegramClient(
        SESSION_NAME,
        api_id,
        api_hash,
    ) as client:

        for username in unique:
            rating = rate_username(username)

            if rating < minimum_rating:
                continue

            # Если здесь возникает FloodWait — сразу выходим.
            status = await check_one(client, username)

            if status == "occupied":
                add_occupied(username)
                occupied.add(username)
                already_checked.add(username)
                print(f"🔴 @{username}")

            elif status == "purchase":
                add_purchase(username)
                purchase.add(username)
                already_checked.add(username)
                print(f"💎 @{username}")

            elif status == "free":
                add_free(username)
                free.add(username)
                already_checked.add(username)
                print(f"🟢 @{username}")

                results.append((username, rating))

                if len(results) >= limit:
                    break

            # INVALID специально не показываем.
            await asyncio.sleep(CHECK_DELAY)

    return results
