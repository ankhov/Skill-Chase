import re
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from bot.database.models import User
from bot.database.db import get_session
from bot.utils.constants import welcome_text, secondary_text
from bot.utils.helpers import create_main_menu

SKILLS, ABOUT, GITHUB, FIELD, PHOTO = range(5)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()

    profile_text = (
        f"- Профиль @{db_user.username}\n\n"
        f"- Навыки: {db_user.skills or 'Не указаны'}\n\n"
        f"- Область деятельности: {db_user.field or 'Не указана'}\n\n"
        f"- О себе: {db_user.about or 'Не заполнено'}\n\n"
        f"- GitHub: {db_user.github or 'Не указан'}"
    )

    keyboard = [
        [InlineKeyboardButton("Изменить навыки", callback_data="edit_skills")],
        [InlineKeyboardButton("Изменить область", callback_data="edit_field")],
        [InlineKeyboardButton("Изменить информацию о себе", callback_data="edit_about")],
        [InlineKeyboardButton("Изменить GitHub", callback_data="edit_github")],
        [InlineKeyboardButton("Изменить аватар", callback_data="edit_photo")],
        [InlineKeyboardButton("Назад", callback_data="back")]
    ]

    if db_user.photo_file_id:
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=db_user.photo_file_id,
            caption=profile_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await query.message.edit_text(profile_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def edit_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.delete()

    user_id = update.callback_query.from_user.id
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        current = user.skills or "не указаны"

    msg = await update.effective_chat.send_message(f"Введи свои навыки (текущие: <i>{current}</i>):", parse_mode="HTML")
    context.user_data["edit_prompt_msg_id"] = msg.message_id
    return SKILLS


async def edit_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.delete()

    user_id = update.callback_query.from_user.id
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        current = user.about or "не заполнено"

    msg = await update.effective_chat.send_message(f"Расскажи о себе (текущие: <i>{current}</i>):", parse_mode="HTML")
    context.user_data["edit_prompt_msg_id"] = msg.message_id
    return ABOUT


async def edit_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.delete()

    user_id = update.callback_query.from_user.id
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        current = user.github or "не указан"

    msg = await update.effective_chat.send_message(f"Введи GitHub (текущий: <i>{current}</i>):", parse_mode="HTML")
    context.user_data["edit_prompt_msg_id"] = msg.message_id
    return GITHUB


async def edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.delete()

    user_id = update.callback_query.from_user.id
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        current = user.field or "не указана"

    msg = await update.effective_chat.send_message(f"Введи область деятельности (текущая: <i>{current}</i>):", parse_mode="HTML")
    context.user_data["edit_prompt_msg_id"] = msg.message_id
    return FIELD


async def edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.delete()
    msg = await update.effective_chat.send_message("Пришли фотографию для аватара:")
    context.user_data["edit_prompt_msg_id"] = msg.message_id
    return PHOTO


async def save_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.delete_message(context.user_data.get("edit_prompt_msg_id"))
    except:
        pass
    await update.message.delete()

    user = update.effective_user
    field = update.message.text.strip().lower()
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.field = field
        session.commit()
    await update.message.chat.send_message("✅ Область деятельности обновлена!", reply_markup=create_main_menu())
    return ConversationHandler.END


async def save_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.delete_message(context.user_data.get("edit_prompt_msg_id"))
    except:
        pass
    await update.message.delete()

    user = update.effective_user
    skills = update.message.text
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.skills = skills
        session.commit()
    await update.message.chat.send_message("✅ Навыки обновлены!", reply_markup=create_main_menu())
    return ConversationHandler.END


async def save_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.delete_message(context.user_data.get("edit_prompt_msg_id"))
    except:
        pass
    await update.message.delete()

    user = update.effective_user
    about = update.message.text
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.about = about
        session.commit()
    await update.message.chat.send_message("✅ Информация обновлена!", reply_markup=create_main_menu())
    return ConversationHandler.END


async def save_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.delete_message(context.user_data.get("edit_prompt_msg_id"))
    except:
        pass
    await update.message.delete()

    github = update.message.text.strip()
    if not re.match(r"^https://(www\.)?github\.com/[A-Za-z0-9_-]+/?$", github):
        await update.message.chat.send_message("❌ Некорректная ссылка. Пример: https://github.com/username")
        return GITHUB

    # Извлекаем имя пользователя из URL
    username = github.rstrip("/").split("/")[-1]

    # Проверка существования пользователя через GitHub API
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.github.com/users/{username}") as response:
            if response.status != 200:
                await update.message.chat.send_message("❌ Пользователь не найден на GitHub.")
                return GITHUB

    user = update.effective_user
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.github = github
        session.commit()

    await update.message.chat.send_message("✅ GitHub обновлён!", reply_markup=create_main_menu())
    return ConversationHandler.END

async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.delete_message(context.user_data.get("edit_prompt_msg_id"))
    except:
        pass
    await update.message.delete()

    user = update.effective_user
    if not update.message.photo:
        await update.message.chat.send_message("Пожалуйста, пришли фотографию.")
        return PHOTO

    photo = update.message.photo[-1]
    file_id = photo.file_id

    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.photo_file_id = file_id
        session.commit()

    await update.message.chat.send_message("✅ Фото обновлено!", reply_markup=create_main_menu())
    return ConversationHandler.END


def register_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(profile, pattern="profile"),
            CallbackQueryHandler(edit_skills, pattern="edit_skills"),
            CallbackQueryHandler(edit_field, pattern="edit_field"),
            CallbackQueryHandler(edit_about, pattern="edit_about"),
            CallbackQueryHandler(edit_github, pattern="edit_github"),
            CallbackQueryHandler(edit_photo, pattern="edit_photo")
        ],
        states={
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_skills)],
            FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_field)],
            ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_about)],
            GITHUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_github)],
            PHOTO: [MessageHandler(filters.PHOTO, save_photo)]
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern="back"))


async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(secondary_text, reply_markup=create_main_menu())
    return ConversationHandler.END
