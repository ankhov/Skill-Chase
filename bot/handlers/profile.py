from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from bot.database.models import User
from bot.database.db import get_session
from bot.utils.helpers import create_main_menu

SKILLS, INTERESTS = range(2)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()

    profile_text = (
        f"Профиль @{db_user.username}\n"
        f"Навыки: {db_user.skills or 'Не указаны'}\n"
        f"Интересы: {db_user.interests or 'Не указаны'}"
    )
    keyboard = [
        [InlineKeyboardButton("Изменить навыки", callback_data="edit_skills")],
        [InlineKeyboardButton("Изменить интересы", callback_data="edit_interests")],
        [InlineKeyboardButton("Назад", callback_data="back")]
    ]
    await query.message.edit_text(profile_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def edit_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Введи свои навыки:")
    return SKILLS

async def edit_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Введи свои интересы:")
    return INTERESTS


async def save_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    skills = update.message.text
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.skills = skills
        session.commit()

    await update.message.reply_text("Навыки обновлены!", reply_markup=create_main_menu())
    return ConversationHandler.END


async def save_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    interests = update.message.text
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.interests = interests
        session.commit()

    await update.message.reply_text("Интересы обновлены!", reply_markup=create_main_menu())
    return ConversationHandler.END



def register_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(profile, pattern="profile"),
            CallbackQueryHandler(edit_skills, pattern="edit_skills"),
            CallbackQueryHandler(edit_interests, pattern="edit_interests")
        ],
        states={
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_skills)],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_interests)],
        },
        fallbacks=[CallbackQueryHandler(profile, pattern="back")]
    )
    application.add_handler(conv_handler)