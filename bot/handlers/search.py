from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler

from sqlalchemy.orm import joinedload

from bot.database.models import User, Item, ItemType
from bot.database.db import get_session
from bot.utils.constants import ITEM_TYPES, MAIN_MENU, welcome_text
from bot.utils.helpers import create_main_menu


# -------- Вспомогательные функции -------- #

def get_user_text(user: User) -> str:
    return (
        f"👤 @{user.username}\n"
        f"🌍 Область: {user.field or 'не указана'}\n"
        f"🧠 Навыки: {user.skills or 'не указаны'}\n"
        f"📝 О себе: {user.about or 'не заполнено'}\n"
        f"🔗 Git: {user.github or 'не указан'}"
    )


def get_item_text(item: Item) -> str:
    username = f"@{item.creator.username}" if item.creator and item.creator.username else "Без имени"
    return (
        f"📌 {item.title}\n"
        f"📝 Описание: {item.description}\n"
        f"🌍 Область: {item.field or 'не указана'}\n"
        f"👤 Создатель: {username}"
    )

def get_navigation_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❤️ Лайк", callback_data=f"{prefix}_like"),
            InlineKeyboardButton("⏭️ Скип", callback_data=f"{prefix}_skip"),
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_prev"),
            InlineKeyboardButton("➡️ Вперёд", callback_data=f"{prefix}_next")
        ],
        [
            InlineKeyboardButton("🏠 В меню", callback_data="back_to_menu")
        ]
    ])


# -------- Поиск пользователей -------- #

async def search_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    with get_session() as session:
        current_user = session.query(User).filter_by(telegram_id=user_id).first()
        if not current_user or not current_user.field:
            await query.message.edit_text("Сначала укажи свою область деятельности в профиле.")
            return

        user_fields = {f.strip().lower() for f in current_user.field.split(",")}
        all_users = session.query(User).filter(
            User.telegram_id != user_id,
            (User.skills != None) | (User.about != None)
        ).all()

        matched = [
            u for u in all_users
            if u.field and user_fields & {f.strip().lower() for f in u.field.split(",")}
        ]

    if not matched:
        await query.message.edit_text("Никто не найден.")
        return

    context.user_data["user_results"] = matched
    context.user_data["user_index"] = 0
    await show_user(update, context)


async def show_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id if query else update.effective_chat.id

    index = context.user_data.get("user_index", 0)
    users = context.user_data.get("user_results", [])
    user = users[index]

    text = get_user_text(user)
    if query:
        await query.message.delete()

    if user.photo_file_id:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=user.photo_file_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=get_navigation_keyboard("user")
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=get_navigation_keyboard("user")
        )


# -------- Поиск айтемов -------- #

async def search_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"search_{key}")]
        for key, text in ITEM_TYPES.items()
    ]
    keyboard.append([InlineKeyboardButton("🏠 В меню", callback_data="back_to_menu")])
    await query.message.edit_text("Выбери тип:", reply_markup=InlineKeyboardMarkup(keyboard))


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

        user_fields = {f.strip().lower() for f in current_user.field.split(",")}
        all_items = session.query(Item).options(joinedload(Item.creator)).filter(Item.type == enum_type).all()

        matched = [
            item for item in all_items
            if item.field and user_fields & {f.strip().lower() for f in item.field.split(",")}
        ]

    if not matched:
        await query.message.edit_text("Ничего не найдено.")
        return

    context.user_data["item_results"] = matched
    context.user_data["item_index"] = 0
    await show_item(update, context)


async def show_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id if query else update.effective_chat.id

    index = context.user_data.get("item_index", 0)
    items = context.user_data.get("item_results", [])
    item = items[index]

    text = get_item_text(item)
    if query:
        await query.message.delete()

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=get_navigation_keyboard("item")
    )


# -------- Обработка лайков/навигации -------- #

async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_menu":
        await query.message.delete()
        await query.message.reply_text(welcome_text, reply_markup=create_main_menu())
        return ConversationHandler.END

    async def notify_end():
        try:
            await query.message.edit_text("Ты просмотрел всех.")
        except:
            await context.bot.send_message(chat_id=query.from_user.id, text="Ты просмотрел всех.")

    if data.startswith("user_"):
        results = context.user_data.get("user_results", [])
        index = context.user_data.get("user_index", 0)
        update_index = lambda i: context.user_data.update({"user_index": i})
        show_func = show_user

        if data == "user_like":
            user = results[index]
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"💌 @{query.from_user.username} заинтересовался твоим профилем!"
                )
            except:
                pass

            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"❤️ Ты лайкнул @{user.username}!"
            )

            index += 1

        elif data in ["user_skip", "user_next"]:
            index += 1
        elif data == "user_prev":
            index -= 1

        if 0 <= index < len(results):
            update_index(index)
            await show_func(update, context)
        else:
            await notify_end()

    elif data.startswith("item_"):
        results = context.user_data.get("item_results", [])
        index = context.user_data.get("item_index", 0)
        update_index = lambda i: context.user_data.update({"item_index": i})
        show_func = show_item

        if data == "item_like":
            item = results[index]
            try:
                await context.bot.send_message(
                    chat_id=item.creator.telegram_id,
                    text=f"💌 @{query.from_user.username} заинтересовался твоей вакансией: <b>{item.title}</b>",
                    parse_mode="HTML"
                )
            except:
                pass

            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"❤️ Ты лайкнул вакансию <b>{item.title}</b>!",
                parse_mode="HTML"
            )

            index += 1

        elif data in ["item_skip", "item_next"]:
            index += 1
        elif data == "item_prev":
            index -= 1

        if 0 <= index < len(results):
            update_index(index)
            await show_func(update, context)
        else:
            await notify_end()


# -------- Регистрация хендлеров -------- #

def register_handlers(application):
    application.add_handler(CallbackQueryHandler(search_item, pattern="search_item"))
    application.add_handler(CallbackQueryHandler(search_by_type, pattern=r"search_(project|hackathon|task|case_championship|olymp)"))
    application.add_handler(CallbackQueryHandler(search_people, pattern="search_people"))
    application.add_handler(CallbackQueryHandler(handle_navigation, pattern=r"^(user|item)_(like|skip|next|prev)$"))
    application.add_handler(CallbackQueryHandler(handle_navigation, pattern="back_to_menu"))
