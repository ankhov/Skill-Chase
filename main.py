from telegram.ext import Application, CallbackQueryHandler

from bot.handlers.profile import back_to_main_menu
from bot.handlers import start, search, create, profile

from config import BOT_TOKEN

def main():
    print("Бот запущен...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    start.register_handlers(application)
    search.register_handlers(application)
    create.register_handlers(application)
    profile.register_handlers(application)

    application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern="back"))

    # Запуск бота
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()