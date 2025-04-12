from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.utils.constants import ITEM_TYPES
from bot.database.models import Item
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

    with get_session() as session:
        items = session.query(Item).filter_by(type=item_type).all()

    if not items:
        await query.message.edit_text("Ничего не найдено.")
        return

    response = f"Найдено ({item_type}):\n\n"
    for item in items:
        response += f"{item.title}\n{item.description}\nСоздатель: @{item.creator.username}\n\n"

    await query.message.edit_text(response, reply_markup=create_main_menu())


def register_handlers(application):
    application.add_handler(CallbackQueryHandler(search_item, pattern="search_item"))
    application.add_handler(CallbackQueryHandler(search_by_type, pattern="search_(project|hackathon|task)"))