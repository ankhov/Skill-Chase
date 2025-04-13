from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.database.models import Item, User
from bot.database.db import get_session


async def my_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    with get_session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await query.message.edit_text("Пользователь не найден.")
            return

        items = session.query(Item).filter_by(creator_id=user.id).all()

    if not items:
        await query.message.edit_text(
            "😕 У вас пока нет созданных вакансий.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 В меню", callback_data="back_to_menu")]
            ])
        )
        return

    await query.message.delete()

    for item in items:
        text = (f"📌 <b>{item.title}</b>\n"
                f"💰 Призовой: <i>{item.prize}</i>\n"
                f"📝 Описание: {item.description[:100]}...")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Удалить вакансию", callback_data=f"delete_item_{item.id}")]
        ])

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Вот ваши вакансии 👆",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 В меню", callback_data="back_to_menu")]
        ])
    )

async def delete_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_id = int(query.data.split("_")[-1])

    with get_session() as session:
        item = session.query(Item).filter_by(id=item_id).first()
        if item:
            session.delete(item)
            session.commit()
            await query.edit_message_text("❌ Вакансия удалена.")
        else:
            await query.answer("Вакансия не найдена.", show_alert=True)
