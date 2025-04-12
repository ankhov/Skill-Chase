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
    user_id = query.from_user.id

    try:
        enum_type = ItemType[item_type.upper()]
    except KeyError:
        await query.message.edit_text("Неверный тип.")
        return

    with get_session() as session:
        current_user = session.query(User).filter_by(telegram_id=user_id).first()

        if not current_user or not current_user.field:
            await query.message.edit_text("Сначала укажи свою область деятельности в профиле.")
            return

        # Преобразуем строку областей пользователя в список (например: "AI, ML, Robotics")
        user_fields = [field.strip().lower() for field in current_user.field.split(",")]

        # Загружаем все элементы нужного типа
        all_items = session.query(Item).options(joinedload(Item.creator))\
            .filter(Item.type == enum_type).all()

        # Оставляем только те, где область элемента входит в список областей пользователя
        items = [
            item for item in all_items
            if item.field and item.field.strip().lower() in user_fields
        ]

    if not items:
        await query.message.edit_text("Ничего не найдено по твоей области.", reply_markup=create_main_menu())
        return

    await query.message.delete()

    for item in items:
        username = f"@{item.creator.username}" if item.creator and item.creator.username else "Без имени"
        text = (
            f"📌 <b>{item.title}</b>\n\n"
            f"- Описание: {item.description}\n\n"
            f"- Область: {item.field or 'не указана'}\n"
            f"-  Создатель: {username}"
        )
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=text,
            parse_mode="HTML"
        )

    welcome_text = (
        f"Привет, {query.from_user.first_name}! 👋\n"
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

    current_user_id = query.from_user.id
    with get_session() as session:
        current_user = session.query(User).filter_by(telegram_id=current_user_id).first()
        if not current_user or not current_user.field:
            await query.message.edit_text("Сначала укажи свою область деятельности в профиле.")
            return

        # Области текущего пользователя
        user_fields = {field.strip().lower() for field in current_user.field.split(",")}

        # Загружаем всех других пользователей
        all_users = session.query(User).filter(
            User.telegram_id != current_user_id,
            (User.skills != None) | (User.about != None)
        ).all()

        # Фильтрация по пересечению областей
        matched_users = []
        for user in all_users:
            if user.field:
                user_fields_set = {f.strip().lower() for f in user.field.split(",")}
                if user_fields & user_fields_set:
                    matched_users.append(user)

    if not matched_users:
        await query.message.edit_text("Никто не найден.")
        return

    await query.message.delete()

    for user in matched_users:
        text = (
            f"@{user.username}\n"
            f"Область: {user.field or 'не указана'}\n"
            f"Навыки: {user.skills or 'не указаны'}\n"
            f"О себе: {user.about or 'не заполнено'}\n"
            f"GitHub: {user.github or 'не указан'}"
        )
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=text
        )

    welcome_text = (
        f"Привет, {query.from_user.first_name}! 👋\n"
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