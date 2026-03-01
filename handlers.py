# handlers.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.validators import validate_phone, validate_email, validate_ip, validate_username
from scrapers.phone_scraper import search_phone
from scrapers.email_scraper import search_email
from scrapers.username_scraper import search_username
from scrapers.ip_scraper import search_ip
from database import save_search, get_search_history
from services.formatter import format_phone_result, format_email_result, format_username_result, format_ip_result
import logging

logger = logging.getLogger(__name__)
search_router = Router()


@search_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🔍 <b>OSINT бот</b>\n"
        "Доступные команды:\n"
        "/phone +79001234567 — поиск по номеру\n"
        "/email user@example.com — поиск по email\n"
        "/username @username — поиск по юзернейму\n"
        "/ip 8.8.8.8 — поиск по IP\n"
        "/history — история поиска\n"
        "/help — справка"
    )


@search_router.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)


@search_router.message(Command("phone"))
async def cmd_phone(message: types.Message):
    query = message.text.replace("/phone", "").strip()
    if not query:
        return await message.answer("❌ Укажите номер: /phone +79001234567")
    if not validate_phone(query):
        return await message.answer("❌ Неверный формат номера. Используйте формат +79001234567")

    msg = await message.answer("⏳ Поиск...")
    try:
        result = await search_phone(query)
        await save_search(message.from_user.id, "phone", query, result)
        formatted = format_phone_result(query, result)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_phone:{query}")]
        ])
        await msg.edit_text(formatted, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Phone search error: {e}")
        await msg.edit_text("❌ Ошибка при поиске. Попробуйте позже.")


@search_router.message(Command("email"))
async def cmd_email(message: types.Message):
    query = message.text.replace("/email", "").strip()
    if not query:
        return await message.answer("❌ Укажите email: /email user@example.com")
    if not validate_email(query):
        return await message.answer("❌ Неверный формат email")

    msg = await message.answer("⏳ Поиск...")
    try:
        result = await search_email(query)
        await save_search(message.from_user.id, "email", query, result)
        formatted = format_email_result(query, result)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_email:{query}")]
        ])
        await msg.edit_text(formatted, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Email search error: {e}")
        await msg.edit_text("❌ Ошибка при поиске. Попробуйте позже.")


@search_router.message(Command("username"))
async def cmd_username(message: types.Message):
    query = message.text.replace("/username", "").strip().lstrip('@')
    if not query:
        return await message.answer("❌ Укажите username: /username @username")
    if not validate_username(query):
        return await message.answer("❌ Неверный формат username (минимум 3 символа, только буквы, цифры и _)")

    msg = await message.answer("⏳ Поиск...")
    try:
        result = await search_username(query)
        await save_search(message.from_user.id, "username", query, result)
        formatted = format_username_result(query, result)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_username:{query}")]
        ])
        await msg.edit_text(formatted, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Username search error: {e}")
        await msg.edit_text("❌ Ошибка при поиске. Попробуйте позже.")


@search_router.message(Command("ip"))
async def cmd_ip(message: types.Message):
    query = message.text.replace("/ip", "").strip()
    if not query:
        return await message.answer("❌ Укажите IP: /ip 8.8.8.8")
    if not validate_ip(query):
        return await message.answer("❌ Неверный формат IP")

    msg = await message.answer("⏳ Поиск...")
    try:
        result = await search_ip(query)
        await save_search(message.from_user.id, "ip", query, result)
        formatted = format_ip_result(query, result)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_ip:{query}")]
        ])
        await msg.edit_text(formatted, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"IP search error: {e}")
        await msg.edit_text("❌ Ошибка при поиске. Попробуйте позже.")


@search_router.message(Command("history"))
async def cmd_history(message: types.Message):
    try:
        history = await get_search_history(message.from_user.id, limit=10)
        if not history:
            return await message.answer("📭 История пуста")

        text = "📜 <b>Последние 10 запросов:</b>\n\n"
        for h in history:
            timestamp = h['timestamp'].strftime('%Y-%m-%d %H:%M') if hasattr(h['timestamp'], 'strftime') else str(
                h['timestamp'])
            text += f"• {h['search_type']}: {h['query']} — {timestamp}\n"
        await message.answer(text)
    except Exception as e:
        logger.error(f"History error: {e}")
        await message.answer("❌ Ошибка при получении истории")


@search_router.callback_query(lambda c: c.data and c.data.startswith("refresh_"))
async def refresh_callback(callback: types.CallbackQuery):
    await callback.answer()
    try:
        cmd, query = callback.data.split(":", 1)
        search_type = cmd.replace("refresh_", "")

        msg = await callback.message.edit_text("⏳ Обновление...")

        if search_type == "phone":
            result = await search_phone(query)
            formatted = format_phone_result(query, result)
        elif search_type == "email":
            result = await search_email(query)
            formatted = format_email_result(query, result)
        elif search_type == "username":
            result = await search_username(query)
            formatted = format_username_result(query, result)
        elif search_type == "ip":
            result = await search_ip(query)
            formatted = format_ip_result(query, result)
        else:
            return

        await msg.edit_text(formatted, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        await callback.message.edit_text("❌ Ошибка при обновлении")