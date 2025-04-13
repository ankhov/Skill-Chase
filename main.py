from telegram.ext import Application, CallbackQueryHandler

from bot.handlers import start, search, create, profile
from bot.handlers.my_vacancies import my_vacancies
from bot.utils.helpers import back_to_main_menu

from config import BOT_TOKEN

def main():
    print("Бот запущен...")
    application = Application.builder().token(BOT_TOKEN).build()

    start.register_handlers(application)
    search.register_handlers(application)
    create.register_handlers(application)
    profile.register_handlers(application)

    application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern="back"))
    application.add_handler(CallbackQueryHandler(my_vacancies, pattern="^my_vacancies$"))

    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()