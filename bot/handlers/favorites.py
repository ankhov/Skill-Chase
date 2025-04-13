from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from sqlalchemy.orm import joinedload

from bot.database.db import get_session
from bot.database.models import User, FavoriteUser, FavoriteItem, Item
from bot.utils.helpers import create_main_menu
from bot.utils.constants import welcome_text


def get_user_text(user: User) -> str:
    return (
        f"👤 @{user.username}\n"
        f"🌍 Область: {user.field or 'не указана'}\n"
        f"🧠 Навыки: {user.skills or 'не указаны'}\n"
        f"📝 О себе: {user.about or 'не заполнено'}\n"
        f"🔗 Git: {user.github or 'не указан'}"
    )


def get_item_text(item) -> str:
    creator = f"@{item.creator.username}" if item.creator and item.creator.username else "Без имени"
    return (
        f"📌 {item.title}\n"
        f"📝 Описание: {item.description}\n"
        f"🌍 Область: {item.field or 'не указана'}\n"
        f"👤 Создатель: {creator}"
    )


def get_fav_keyboard(prefix, index) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌ Удалить", callback_data=f"{prefix}_remove_{index}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_prev"),
            InlineKeyboardButton("➡️ Вперёд", callback_data=f"{prefix}_next")
        ],
        [
            InlineKeyboardButton("🏠 В меню", callback_data="back_to_menu")
        ]
    ])


# ---------- Просмотр избранного ---------- #

async def show_favorite_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        favorites = [f.favorite_user for f in user.favorite_users]

    if not favorites:
        await query.message.edit_text("У тебя нет избранных пользователей.")
        return

    context.user_data["fav_users"] = favorites
    context.user_data["fav_users_index"] = 0
    await display_fav_user(update, context)


async def display_fav_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    index = context.user_data.get("fav_users_index", 0)
    favorites = context.user_data.get("fav_users", [])

    if not favorites:
        await query.message.edit_text("Список пуст.")
        return

    user = favorites[index]
    text = get_user_text(user)
    chat_id = query.message.chat.id

    await query.message.delete()

    if user.photo_file_id:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=user.photo_file_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=get_fav_keyboard("favuser", index)
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=get_fav_keyboard("favuser", index)
        )


async def show_favorite_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()

        favorites = session.query(FavoriteItem).options(
            joinedload(FavoriteItem.item).joinedload(Item.creator)
        ).filter_by(user_id=user.id).all()

        items = [f.item for f in favorites]

    if not items:
        await query.message.edit_text("У тебя нет избранных айтемов.")
        return

    context.user_data["fav_items"] = items
    context.user_data["fav_items_index"] = 0
    await display_fav_item(update, context)


async def display_fav_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    index = context.user_data.get("fav_items_index", 0)
    favorites = context.user_data.get("fav_items", [])

    if not favorites:
        await query.message.edit_text("Список пуст.")
        return

    item = favorites[index]
    text = get_item_text(item)
    chat_id = query.message.chat.id

    await query.message.delete()
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=get_fav_keyboard("favitem", index)
    )


# ---------- Навигация и удаление ---------- #

async def handle_fav_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    def update_index(key, delta):
        index = context.user_data.get(f"{key}_index", 0) + delta
        results = context.user_data.get(f"{key}", [])
        if 0 <= index < len(results):
            context.user_data[f"{key}_index"] = index
            return True
        return False

    if data == "back_to_menu":
        await query.message.delete()
        await query.message.reply_text(welcome_text, reply_markup=create_main_menu())
        return

    if data.startswith("favuser_"):
        if "_prev" in data:
            if update_index("fav_users", -1):
                await display_fav_user(update, context)
        elif "_next" in data:
            if update_index("fav_users", 1):
                await display_fav_user(update, context)
        elif "_remove_" in data:
            index = int(data.split("_")[-1])
            current = context.user_data.get("fav_users", [])[index]
            user_id = query.from_user.id
            with get_session() as session:
                me = session.query(User).filter_by(telegram_id=user_id).first()
                fav = session.query(FavoriteUser).filter_by(user_id=me.id, favorite_user_id=current.id).first()
                if fav:
                    session.delete(fav)
                    session.commit()
            context.user_data["fav_users"].pop(index)
            if context.user_data["fav_users"]:
                context.user_data["fav_users_index"] = min(index, len(context.user_data["fav_users"]) - 1)
                await display_fav_user(update, context)
            else:
                await query.message.edit_text("Список избранных пользователей пуст.")

    elif data.startswith("favitem_"):
        if "_prev" in data:
            if update_index("fav_items", -1):
                await display_fav_item(update, context)
        elif "_next" in data:
            if update_index("fav_items", 1):
                await display_fav_item(update, context)
        elif "_remove_" in data:
            index = int(data.split("_")[-1])
            current = context.user_data.get("fav_items", [])[index]
            user_id = query.from_user.id
            with get_session() as session:
                me = session.query(User).filter_by(telegram_id=user_id).first()
                fav = session.query(FavoriteItem).filter_by(user_id=me.id, item_id=current.id).first()
                if fav:
                    session.delete(fav)
                    session.commit()
            context.user_data["fav_items"].pop(index)
            if context.user_data["fav_items"]:
                context.user_data["fav_items_index"] = min(index, len(context.user_data["fav_items"]) - 1)
                await display_fav_item(update, context)
            else:
                await query.message.edit_text("Список избранных айтемов пуст.")


def register_favorites_handlers(application):
    application.add_handler(CallbackQueryHandler(show_favorite_users, pattern="show_fav_users"))
    application.add_handler(CallbackQueryHandler(show_favorite_items, pattern="show_fav_items"))
    application.add_handler(CallbackQueryHandler(handle_fav_navigation, pattern=r"fav(user|item)_(prev|next|remove_\d+)"))
    application.add_handler(CallbackQueryHandler(handle_fav_navigation, pattern="back_to_menu"))
