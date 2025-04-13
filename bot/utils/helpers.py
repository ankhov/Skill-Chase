from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.utils.constants import MAIN_MENU, welcome_text


def create_main_menu():
    keyboard = [
        [InlineKeyboardButton(text, callback_data=key)] for key, text in MAIN_MENU.items()
    ]
    return InlineKeyboardMarkup(keyboard)

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(welcome_text, reply_markup=create_main_menu())
    return ConversationHandler.END
