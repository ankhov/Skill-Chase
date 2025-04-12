from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from bot.database.models import User
from bot.database.db import get_session
from bot.utils.helpers import create_main_menu

SKILLS, INTERESTS, GITHUB, FIELD = range(4)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()

    profile_text = (
        f"- Профиль @{db_user.username}\n\n"
        f"- Навыки: {db_user.skills or 'Не указаны'}\n\n"
        f"- Область деятельности: {db_user.field or "Не указана"}\n\n"
        f"- О себе: {db_user.about or 'Не заполнено'}\n\n"
        f"- GitHub: {db_user.github or 'Не указан'}"
    )
    keyboard = [
        [InlineKeyboardButton("Изменить навыки", callback_data="edit_skills")],
        [InlineKeyboardButton("Изменить область", callback_data="edit_field")],
        [InlineKeyboardButton("Изменить информацию о себе", callback_data="edit_about")],
        [InlineKeyboardButton("Изменить GitHub", callback_data="edit_github")],
        [InlineKeyboardButton("Назад", callback_data="back")]
    ]
    await query.message.edit_text(profile_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def edit_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Введи свои навыки:")
    return SKILLS

async def edit_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Расскажи о себе:")
    return INTERESTS

async def edit_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Введи свой GitHub (например, https://github.com/username):")
    return GITHUB

async def edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Введи свою область деятельности:")
    return FIELD

async def save_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    field = update.message.text.strip().lower()
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.field = field
        session.commit()
    await update.message.reply_text("Область деятельности обновлена!", reply_markup=create_main_menu())
    return ConversationHandler.END

async def save_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    skills = update.message.text
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.skills = skills
        session.commit()

    await update.message.reply_text("Навыки обновлены!", reply_markup=create_main_menu())
    return ConversationHandler.END


async def save_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    interests = update.message.text
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.interests = interests
        session.commit()

    await update.message.reply_text("Информация обновлена!", reply_markup=create_main_menu())
    return ConversationHandler.END


async def save_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    github = update.message.text
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.github = github
        session.commit()

    await update.message.reply_text("GitHub обновлён!", reply_markup=create_main_menu())
    return ConversationHandler.END
def register_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(profile, pattern="profile"),
            CallbackQueryHandler(edit_skills, pattern="edit_skills"),
            CallbackQueryHandler(edit_field, pattern="edit_field"),
            CallbackQueryHandler(edit_about, pattern="edit_about"),
            CallbackQueryHandler(edit_github, pattern="edit_github")
        ],
        states={
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_skills)],
            FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_field)],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_about)],
            GITHUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_github)],
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)

    application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern="back"))


async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n"
        "Я бот для поиска проектов, хакатонов, задач и людей для совместной работы.\n"
        "Что хочешь сделать?"
    )
    await query.answer()
    await query.message.edit_text(welcome_text, reply_markup=create_main_menu())
    return ConversationHandler.END