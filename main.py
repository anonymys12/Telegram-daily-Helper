import os
import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv

# Завантажуємо токен з .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привіт! 👋 Я твій Daily Helper бот.\n"
        "Команди:\n"
        "/quote — мотиваційна цитата дня\n"
        "/help — список команд"
    )

# Команда /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Доступні команди:\n"
        "/start — почати роботу\n"
        "/quote — отримати цитату дня"
    )

# Команда /quote
def quote(update: Update, context: CallbackContext):
    quotes = [
        "Успіх приходить до тих, хто діє, а не чекає.",
        "Кожен день — новий шанс змінити своє життя.",
        "Не бійся почати спочатку. Це твій шанс створити щось краще.",
        "Дисципліна перемагає мотивацію.",
        "Твій майбутній успіх залежить від сьогоднішніх дій."
    ]
    update.message.reply_text(random.choice(quotes))

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("quote", quote))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
