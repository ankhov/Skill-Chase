from telegram.ext import Application
from config import BOT_TOKEN
from bot.handlers import start, search, create, profile


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    start.register_handlers(application)
    search.register_handlers(application)
    create.register_handlers(application)
    profile.register_handlers(application)

    # Запуск бота
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()