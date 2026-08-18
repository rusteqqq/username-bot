import asyncio
import time
from pathlib import Path

from telethon import TelegramClient, errors, functions

from config import SESSION_NAMES, CHECK_DELAY
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
        raise ScannerCooldown(e.seconds)

    except Exception as e:
        print(f"⚠️ {type(e).__name__}: {e}")
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

    # =========================================================
    # СОЗДАЁМ ВСЕ СЕССИИ
    # =========================================================

    accounts = []

    for session_name in SESSION_NAMES:
        client = TelegramClient(
            session_name,
            api_id,
            api_hash,
        )

        await client.connect()

        if not await client.is_user_authorized():
            await client.disconnect()

            raise RuntimeError(
                f"Сессия '{session_name}' не авторизована. "
                f"Авторизуйте её на ПК и загрузите .session файл."
            )

        accounts.append({
            "name": session_name,
            "client": client,
            "cooldown_until": 0.0,
        })

        print(f"🟢 Сессия подключена: {session_name}")

    if not accounts:
        raise RuntimeError("Нет доступных Telegram-сессий.")

    # Индекс для последовательной ротации:
    # 0 → 1 → 2 → 0 → ...
    next_account_index = 0

    try:

        # =====================================================
        # ОСНОВНОЙ ЦИКЛ
        # =====================================================

        username_index = 0

        while username_index < len(unique):

            username = unique[username_index]

            rating = rate_username(username)

            if rating < minimum_rating:
                username_index += 1
                continue

            # -------------------------------------------------
            # Ищем доступную сессию.
            # -------------------------------------------------

            account = None

            for _ in range(len(accounts)):
                candidate = accounts[next_account_index]

                next_account_index = (
                    next_account_index + 1
                ) % len(accounts)

                if candidate["cooldown_until"] <= time.time():
                    account = candidate
                    break

            # -------------------------------------------------
            # Все сессии получили FloodWait.
            # -------------------------------------------------

            if account is None:

                now = time.time()

                next_available = min(
                    account["cooldown_until"]
                    for account in accounts
                )

                wait_time = max(
                    1,
                    int(next_available - now)
                )

                print(
                    f"⏳ Все 3 сессии на cooldown. "
                    f"Ждём {wait_time} сек."
                )

                await asyncio.sleep(wait_time)

                continue

            client = account["client"]
            session_name = account["name"]

            # -------------------------------------------------
            # Проверяем username.
            # -------------------------------------------------

            try:

                status = await check_one(
                    client,
                    username,
                )

            except ScannerCooldown as e:

                account["cooldown_until"] = (
                    time.time() + e.seconds
                )

                print(
                    f"⏳ {session_name}: FloodWait "
                    f"{e.seconds} сек."
                )

                # ВАЖНО:
                # username НЕ увеличиваем.
                #
                # Поэтому следующий доступный аккаунт
                # проверит ТОТ ЖЕ username.
                continue

            # -------------------------------------------------
            # Результаты
            # -------------------------------------------------

            if status == "occupied":

                add_occupied(username)

                occupied.add(username)
                already_checked.add(username)

                print(
                    f"🔴 @{username} "
                    f"[{session_name}]"
                )

            elif status == "purchase":

                add_purchase(username)

                purchase.add(username)
                already_checked.add(username)

                print(
                    f"💎 @{username} "
                    f"[{session_name}]"
                )

            elif status == "free":

                add_free(username)

                free.add(username)
                already_checked.add(username)

                print(
                    f"🟢 @{username} "
                    f"[{session_name}]"
                )

                results.append(
                    (username, rating)
                )

                if len(results) >= limit:
                    break

            elif status == "invalid":

                print(
                    f"⚪ @{username} "
                    f"[{session_name}]"
                )

            elif status == "error":

                print(
                    f"⚠️ Ошибка проверки "
                    f"@{username} "
                    f"[{session_name}]"
                )

            # Только после успешной проверки
            # переходим к следующему username.
            username_index += 1

            await asyncio.sleep(CHECK_DELAY)

    finally:

        # =====================================================
        # ОТКЛЮЧАЕМ ВСЕ СЕССИИ
        # =====================================================

        for account in accounts:

            try:
                await account["client"].disconnect()

            except Exception:
                pass

    return results
