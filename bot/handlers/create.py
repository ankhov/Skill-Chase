from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from bot.utils.constants import ITEM_TYPES
from bot.database.models import Item, ItemType, User
from bot.database.db import get_session
from bot.utils.helpers import create_main_menu

TITLE, PRIZE, DESCRIPTION, TYPE, FIELD = range(5)


async def create_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"type_{key}")]
        for key, text in ITEM_TYPES.items()
    ]
    keyboard.append([InlineKeyboardButton("🏠 В меню", callback_data="back_to_menu")])
    await query.message.edit_text(
        "Выбери тип:", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TYPE


async def set_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["type"] = query.data.replace("type_", "")
    await query.message.edit_text("Введи название:")
    return TITLE


async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введи призовой:")
    return PRIZE

async def set_prize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["prize"] = update.message.text
    await update.message.reply_text("Введи описание:")
    return DESCRIPTION

async def set_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Введи область деятельности для этой темы (например, ИИ, дизайн, финтех и т.д.):")
    return FIELD


async def set_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    field = update.message.text
    context.user_data["field"] = field

    title = context.user_data["title"]
    prize = context.user_data["prize"]
    description = context.user_data["description"]
    item_type = context.user_data["type"]

    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        new_item = Item(
            type=ItemType[item_type.upper()],
            title=title,
            prize=prize,
            description=description,
            field=field,
            creator_id=db_user.id
        )
        session.add(new_item)
        session.commit()

    await update.message.reply_text(
        f"{ITEM_TYPES[item_type]} успешно создан!",
        reply_markup=create_main_menu()
    )
    return ConversationHandler.END



def register_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_item, pattern="create_item")],
        states={
            TYPE: [CallbackQueryHandler(set_type, pattern="type_(project|hackathon|task|case_championship|olymp)")],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_title)],
            PRIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_prize)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_description)],
            FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_field)],
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)
