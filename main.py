import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv

# Завантажуємо токени з .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привіт! Я твій Daily Helper бот. Використовуй команди, щоб отримати допомогу!")

def main():
    # Створюємо Updater
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    # Додаємо CommandHandler для /start
    dp.add_handler(CommandHandler("start", start))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
