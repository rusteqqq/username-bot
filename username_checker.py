# Реальная проверка находится в scanner.py.
# Этот файл оставлен как совместимый модуль проекта.

from scanner import check_one

async def check_username(client, username):
    return await check_one(client, username)
