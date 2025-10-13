import os
import random
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Отримуємо токени з .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Простий список задач
todo_list = []

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привіт! Я твій Daily Helper бот.")

def todo(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Введи задачу після команди /todo")
        return
    task = " ".join(context.args)
    todo_list.append(task)
    update.message.reply_text(f"Задача додана: {task}")

def list_tasks(update: Update, context: CallbackContext):
    if not todo_list:
        update.message.reply_text("Список задач порожній.")
    else:
        tasks = "\n".join([f"{i+1}. {t}" for i, t in enumerate(todo_list)])
        update.message.reply_text(f"Список задач:\n{tasks}")

def quote(update: Update, context: CallbackContext):
    quotes = [
        "Ніколи не здавайся!",
        "Кожен день — шанс стати кращим.",
        "Просто почни робити."
    ]
    update.message.reply_text(random.choice(quotes))

def weather(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Введи місто після команди /weather")
        return
    city = " ".join(context.args)
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]
        update.message.reply_text(f"Погода в {city}: {temp}°C, {desc}")
    except:
        update.message.reply_text("Не вдалося отримати погоду.")

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("todo", todo))
    dp.add_handler(CommandHandler("list", list_tasks))
    dp.add_handler(CommandHandler("quote", quote))
    dp.add_handler(CommandHandler("weather", weather))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
