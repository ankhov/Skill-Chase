from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.utils.helpers import create_main_menu
from bot.database.models import User
from bot.database.db import get_session


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        if not db_user:
            db_user = User(telegram_id=user.id, username=user.username)
            session.add(db_user)
            session.commit()

    welcome_text = (
        f"Привет, {user.first_name}! 👋\n"
        "Я бот для поиска проектов, хакатонов, задач и людей для совместной работы.\n"
        "Что хочешь сделать?"
    )
    await update.message.reply_text(welcome_text, reply_markup=create_main_menu())


def register_handlers(application):
    application.add_handler(CommandHandler("start", start))