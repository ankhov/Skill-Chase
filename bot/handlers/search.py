from sqlalchemy.orm import joinedload
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.utils.constants import ITEM_TYPES
from bot.database.models import Item, User, ItemType
from bot.database.db import get_session
from bot.utils.helpers import create_main_menu


async def search_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"search_{key}")]
        for key, text in ITEM_TYPES.items()
    ]
    await query.message.edit_text(
        "Выбери тип:", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def search_by_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_type = query.data.replace("search_", "")

    try:
        enum_type = ItemType[item_type.upper()]
    except KeyError:
        await query.message.edit_text("Неверный тип.")
        return

    with get_session() as session:
        items = session.query(Item).options(joinedload(Item.creator))\
            .filter_by(type=enum_type).all()

    if not items:
        await query.message.edit_text("Ничего не найдено.", reply_markup=create_main_menu())
        return

    await query.message.delete()  # Удаляем сообщение с кнопками выбора типа

    for item in items:
        username = f"@{item.creator.username}" if item.creator and item.creator.username else "Без имени"
        text = f"📌 <b>{item.title}</b>\n\n{item.description}\n\n👤 Создатель: {username}"
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=text,
            parse_mode="HTML"
        )

    user = update.effective_user
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n"
        "Я бот для поиска проектов, хакатонов, задач и людей для совместной работы.\n"
        "Что хочешь сделать?"
    )

    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text=welcome_text,
        reply_markup=create_main_menu()
    )

async def search_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    with get_session() as session:
        users = session.query(User).filter(
            (User.skills != None) | (User.interests != None)
        ).all()

    if not users:
        await query.message.edit_text("Никто не найден.")
        return

    await query.message.delete()

    for user in users:
        text = (
            f"@{user.username}\n"
            f"Навыки: {user.skills or 'не указаны'}\n"
            f"Интересы: {user.interests or 'не указаны'}\n"
            f"GitHub: {user.github or 'не указан'}"
        )
        await query.message.chat.send_message(text)

    user = update.effective_user
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n"
        "Я бот для поиска проектов, хакатонов, задач и людей для совместной работы.\n"
        "Что хочешь сделать?"
    )

    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text=welcome_text,
        reply_markup=create_main_menu()
    )


def register_handlers(application):
    application.add_handler(CallbackQueryHandler(search_item, pattern="search_item"))
    application.add_handler(CallbackQueryHandler(search_by_type, pattern="search_(project|hackathon|task|case_championship|olymp)"))
    application.add_handler(CallbackQueryHandler(search_people, pattern="search_people"))