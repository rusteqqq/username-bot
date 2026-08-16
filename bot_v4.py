import asyncio
import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, API_ID, API_HASH
from database import init_db
from generator import generate_candidates
from price_estimator import estimate_price
from scanner import find_free_usernames, ScannerCooldown
from traps import add_trap, get_traps
from free_archive import load_free

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

MENU = """⚡️ ПОИСК СВОБОДНЫХ НИКОВ
━━━━━━━━━━━━━━━━━

• 5 / 6 / 7-буквенные ники
• Свободная маска от 5 до 8 букв
• Фильтр по рейтингу
• Ловушки
• Архив найденных ников

Выберите действие 👇"""

REPLY_KEYBOARD = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton("💎 5 букв"),
            KeyboardButton("💠 6 букв"),
            KeyboardButton("🔷 7 букв"),
        ],
        [
            KeyboardButton("⭐ Топ 7/10+"),
            KeyboardButton("🎯 По маске"),
        ],
        [
            KeyboardButton("📚 Все свободные"),
            KeyboardButton("👁 Мои ловушки"),
        ],
        [
            KeyboardButton("⛔ Остановить поиск"),
            KeyboardButton("ℹ️ Помощь"),
        ],
    ],
    resize_keyboard=True,
    is_persistent=True,
    input_field_placeholder="Выберите действие...",
)

RESULT_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("🔄 Ещё 5 букв", callback_data="find5"),
            InlineKeyboardButton("📚 Архив", callback_data="allfree"),
        ]
    ]
)


def format_wait(seconds):
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)

    if hours:
        return f"{hours} ч. {minutes} мин."
    if minutes:
        return f"{minutes} мин."
    return f"{secs} сек."


def format_result(username, rating):
    price = estimate_price(rating, len(username))

    if isinstance(price, (tuple, list)) and len(price) >= 2:
        low, high = price[0], price[1]
        price_text = f"${low:.0f}-${high:.0f}"
    else:
        price_text = f"≈ ${float(price):.0f}"

    return (
        f"✅ НИК НАЙДЕН!  @{username}\n\n"
        f"├ Читабельность — {rating}/10\n"
        f"├ Примерная цена — {price_text}\n"
        f"├ Ликвидность — {rating}/10\n"
        f"└ ⚡️ СВОБОДЕН"
    )


def get_task(context):
    return context.application.bot_data.get("scan_task")


def set_task(context, task):
    context.application.bot_data["scan_task"] = task


async def stop_search(context):
    task = get_task(context)

    if task and not task.done():
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        set_task(context, None)
        return True

    return False


async def run_search(
    message,
    context,
    minimum_rating=0,
    count=5,
    length=5,
    mask=None,
):
    old_task = get_task(context)

    if old_task and not old_task.done():
        await message.reply_text(
            "🔎 Поиск уже идёт.\n\n"
            "Нажми «⛔ Остановить поиск», чтобы остановить его.",
            reply_markup=REPLY_KEYBOARD,
        )
        return

    async def worker():
        if mask:
            candidates = generate_candidates(
                120,
                length,
                mask=mask,
            )
        else:
            candidates = generate_candidates(
                120,
                length,
            )

        return await find_free_usernames(
            candidates,
            API_ID,
            API_HASH,
            minimum_rating=minimum_rating,
            limit=count,
        )

    task = asyncio.create_task(worker())
    set_task(context, task)

    try:
        free = await task

    except asyncio.CancelledError:
        return

    except ScannerCooldown as e:
        await message.reply_text(
            "⏳ TELEGRAM ВРЕМЕННО ОГРАНИЧИЛ ПРОВЕРКИ\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            f"Повторить поиск можно примерно через:\n"
            f"🕐 {format_wait(e.seconds)}\n\n"
            "Поиск остановлен автоматически.\n"
            "Остальные кнопки продолжают работать.",
            reply_markup=REPLY_KEYBOARD,
        )
        return

    except Exception as e:
        logging.exception("Search error")
        await message.reply_text(
            f"⚠️ Поиск остановлен.\nПричина: {type(e).__name__}",
            reply_markup=REPLY_KEYBOARD,
        )
        return

    finally:
        current = get_task(context)
        if current is task:
            set_task(context, None)

    if not free:
        await message.reply_text(
            "❌ Подходящих свободных ников не найдено.",
            reply_markup=REPLY_KEYBOARD,
        )
        return

    text = "\n\n".join(
        format_result(username, rating)
        for username, rating in free
    )

    await message.reply_text(
        text,
        reply_markup=RESULT_KEYBOARD,
    )


async def show_all_free(message):
    free = load_free()

    if not free:
        await message.reply_text(
            "📚 Архив свободных пока пуст.",
            reply_markup=REPLY_KEYBOARD,
        )
        return

    shown = free[-1000:]

    text = (
        "📚 ВСЕ НАЙДЕННЫЕ СВОБОДНЫЕ\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"Всего сохранено: {len(free)}\n\n"
        + "\n".join(f"• @{u}" for u in shown)
    )

    if len(free) > 1000:
        text += "\n\nПоказаны последние 1000."

    await message.reply_text(
        text,
        reply_markup=REPLY_KEYBOARD,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_mask"] = False

    await update.message.reply_text(
        MENU,
        reply_markup=REPLY_KEYBOARD,
    )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stopped = await stop_search(context)

    if stopped:
        await update.message.reply_text(
            "⛔ Поиск остановлен.",
            reply_markup=REPLY_KEYBOARD,
        )
    else:
        await update.message.reply_text(
            "ℹ️ Сейчас активного поиска нет.",
            reply_markup=REPLY_KEYBOARD,
        )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "find5":
        await query.edit_message_text(
            "🔎 Ищу лучшие 5-буквенные варианты..."
        )
        await run_search(
            query.message,
            context,
            minimum_rating=0,
            count=5,
            length=5,
        )

    elif query.data == "allfree":
        await show_all_free(query.message)


async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "⛔ Остановить поиск":
        await stop_command(update, context)
        return

    length_buttons = {
        "💎 5 букв": 5,
        "💠 6 букв": 6,
        "🔷 7 букв": 7,
    }

    if text in length_buttons:
        length = length_buttons[text]

        await update.message.reply_text(
            f"🔎 Генерирую лучшие {length}-буквенные варианты...\n"
            "🧠 Сначала жёстко фильтрую кандидатов локально, "
            "потом проверяю Telegram.",
            reply_markup=REPLY_KEYBOARD,
        )

        await run_search(
            update.message,
            context,
            minimum_rating=0,
            count=5,
            length=length,
        )
        return

    if text == "⭐ Топ 7/10+":
        await update.message.reply_text(
            "⭐ Ищу только варианты с рейтингом 7/10+...",
            reply_markup=REPLY_KEYBOARD,
        )

        await run_search(
            update.message,
            context,
            minimum_rating=7.0,
            count=5,
            length=5,
        )
        return

    if text == "🎯 По маске":
        context.user_data["waiting_mask"] = True

        await update.message.reply_text(
            "🎯 ОТПРАВЬ МАСКУ\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "От 5 до 8 символов.\n"
            "`?` = любая буква.\n\n"
            "Примеры:\n"
            "`a????`\n"
            "`a?b?c`\n"
            "`??z??`\n"
            "`?a??e?`",
            parse_mode="Markdown",
            reply_markup=REPLY_KEYBOARD,
        )
        return

    if text == "📚 Все свободные":
        await show_all_free(update.message)
        return

    if text == "👁 Мои ловушки":
        traps = get_traps(update.effective_user.id)

        if traps:
            text_out = (
                "👁 ТВОИ ЛОВУШКИ\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                + "\n".join(f"• @{u}" for u in traps)
            )
        else:
            text_out = "👁 Ловушек пока нет."

        await update.message.reply_text(
            text_out,
            reply_markup=REPLY_KEYBOARD,
        )
        return

    if text == "ℹ️ Помощь":
        await update.message.reply_text(
            "ℹ️ ПОМОЩЬ\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "💎 5 букв — редкие 5-буквенные.\n"
            "💠 6 букв — редкие 6-буквенные.\n"
            "🔷 7 букв — редкие 7-буквенные.\n"
            "⭐ Топ 7/10+ — высокий рейтинг.\n"
            "🎯 По маске — любая комбинация длиной 5–8.\n"
            "📚 Все свободные — накопленный архив.\n"
            "⛔ Остановить поиск — отменяет текущий поиск.",
            reply_markup=REPLY_KEYBOARD,
        )
        return

    if context.user_data.get("waiting_mask"):
        context.user_data["waiting_mask"] = False
        mask = text.lower()

        if not (5 <= len(mask) <= 8):
            await update.message.reply_text(
                "❌ Маска должна быть от 5 до 8 символов.",
                reply_markup=REPLY_KEYBOARD,
            )
            return

        if any(c not in "abcdefghijklmnopqrstuvwxyz?" for c in mask):
            await update.message.reply_text(
                "❌ Используй только латинские a-z и знак ?.",
                reply_markup=REPLY_KEYBOARD,
            )
            return

        await update.message.reply_text(
            f"🎯 Маска `{mask}`\n"
            "🔎 Подбираю лучшие варианты...",
            parse_mode="Markdown",
            reply_markup=REPLY_KEYBOARD,
        )

        await run_search(
            update.message,
            context,
            minimum_rating=0,
            count=7,
            length=len(mask),
            mask=mask,
        )
        return

    if text.startswith("@"):
        username = text[1:].lower()

        if (
            5 <= len(username) <= 32
            and all(c.isalnum() or c == "_" for c in username)
        ):
            add_trap(username, update.effective_user.id)

            await update.message.reply_text(
                f"👁 @{username} добавлен в ловушки.",
                reply_markup=REPLY_KEYBOARD,
            )
            return

    await update.message.reply_text(
        MENU,
        reply_markup=REPLY_KEYBOARD,
    )


def main():
    if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Не указан BOT_TOKEN в config.py")

    if (
        not API_ID
        or not API_HASH
        or API_HASH == "PASTE_YOUR_API_HASH_HERE"
    ):
        raise RuntimeError("Не указаны API_ID/API_HASH в config.py")

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            messages,
        )
    )

    print("✅ Бот запущен.")
    print("⌨️ Кнопки меню доступны прямо в чате.")

    app.run_polling()


if __name__ == "__main__":
    main()
