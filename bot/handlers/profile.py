import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from bot.database.models import User
from bot.database.db import get_session
from bot.utils.constants import welcome_text, secondary_text
from bot.utils.helpers import create_main_menu

SKILLS, ABOUT, REPO, FIELD, PHOTO = range(5)


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
        f"- Репозиторий: {db_user.github or 'Не указан'}"
    )

    keyboard = [
        [InlineKeyboardButton("Изменить навыки", callback_data="edit_skills")],
        [InlineKeyboardButton("Изменить область", callback_data="edit_field")],
        [InlineKeyboardButton("Изменить информацию о себе", callback_data="edit_about")],
        [InlineKeyboardButton("Изменить репозиторий", callback_data="edit_repo")],
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


async def edit_repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.delete()

    user_id = update.callback_query.from_user.id
    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        current = user.github or "не указан"

    msg = await update.effective_chat.send_message(
        f"Введи ссылку на GitHub или GitLab (текущая: <i>{current}</i>):", parse_mode="HTML"
    )
    context.user_data["edit_prompt_msg_id"] = msg.message_id
    return REPO


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


async def save_repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.delete_message(context.user_data.get("edit_prompt_msg_id"))
    except:
        pass
    await update.message.delete()

    repo_url = update.message.text.strip()

    # Проверяем, что URL начинается с https://
    if not repo_url.startswith("https://"):
        await update.message.chat.send_message(
            "❌ Ссылка должна начинаться с https://. Примеры: https://github.com/username, https://gitlab.com/username"
        )
        return REPO

    # Извлекаем домен и имя пользователя
    try:
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 4:
            raise ValueError
        domain = parts[2]  # Например, github.com, gitlab.com, gitlab.informatics.ru
        username = parts[3]  # Имя пользователя
    except (IndexError, ValueError):
        await update.message.chat.send_message(
            "❌ Некорректный формат ссылки. Примеры: https://github.com/username, https://gitlab.com/username"
        )
        return REPO

    # Проверка через API
    async with aiohttp.ClientSession() as session:
        try:
            if "github.com" in domain:
                # Проверка GitHub
                async with session.get(f"https://api.github.com/users/{username}") as response:
                    if response.status != 200:
                        await update.message.chat.send_message("❌ Пользователь не найден на GitHub.")
                        return REPO
            elif "gitlab" in domain.lower():
                # Проверка GitLab
                if domain == "gitlab.com" or domain == "www.gitlab.com":
                    async with session.get(f"https://gitlab.com/api/v4/users?username={username}") as response:
                        if response.status != 200 or not await response.json():
                            await update.message.chat.send_message("❌ Пользователь не найден на GitLab.")
                            return REPO
                else:
                    # Для кастомных GitLab-доменов пробуем получить страницу профиля
                    async with session.get(f"{repo_url.rstrip('/')}", headers={"Accept": "text/html"}) as response:
                        if response.status != 200:
                            await update.message.chat.send_message(
                                f"❌ Пользователь не найден на {domain}."
                            )
                            return REPO
                        # Проверяем, что страница не возвращает ошибку (например, 404 в теле ответа)
                        content = await response.text()
                        if "404" in content or "Not Found" in content:
                            await update.message.chat.send_message(
                                f"❌ Пользователь не найден на {domain}."
                            )
                            return REPO
            else:
                await update.message.chat.send_message(
                    "❌ Ссылка должна быть на GitHub или GitLab. Примеры: https://github.com/username, https://gitlab.com/username"
                )
                return REPO
        except aiohttp.ClientError:
            await update.message.chat.send_message("❌ Ошибка проверки. Попробуй позже.")
            return REPO

    user = update.effective_user
    with get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        db_user.github = repo_url  # Поле остаётся github для совместимости
        session.commit()

    await update.message.chat.send_message("✅ Репозиторий обновлён!", reply_markup=create_main_menu())
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
            CallbackQueryHandler(edit_repo, pattern="edit_repo"),
            CallbackQueryHandler(edit_photo, pattern="edit_photo")
        ],
        states={
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_skills)],
            FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_field)],
            ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_about)],
            REPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_repo)],
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