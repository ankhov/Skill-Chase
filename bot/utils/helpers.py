from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.utils.constants import MAIN_MENU

def create_main_menu():
    keyboard = [
        [InlineKeyboardButton(text, callback_data=key)] for key, text in MAIN_MENU.items()
    ]
    return InlineKeyboardMarkup(keyboard)