import os
import random
from datetime import time as dt_time
from aiohttp import ClientSession
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

from cities_by_region import CITIES_BY_REGION  # словник областей та міст

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

USER_CITY = {}  # {chat_id: "Київ"}

# -----------------------------
# Клас фраз
# -----------------------------
class MemePhrases:
    def __init__(self):
        self.phrases = [
            "Життя — цікаве, і мотивація то є сильна",
            "Ярик, бачок потік",
            "Ці руки нічого не крали",
            "Разом нас багато — нас не подолати",
            "Може я тоже хочу шоколадку",
            "Я хапанула",
            "Штани за 40 гривень",
            "А еслі б я не сохранився?",
            "Ну, мені нравиться, як воно горить...",
            "Я не з такої сім’ї, а з богатої",
            "Хто не скаче, той москаль",
            "Це мерзость!",
            "Щоб вода перетворилася на гарячу — її треба підігріти",
            "Хто не чув — той побачить",
            "Не говорити про погане. Краще – зробити",
            "Що поганого, що я підтримую цих страусів?"
        ]

    def get_random_phrase(self):
        return random.choice(self.phrases)

meme_bot = MemePhrases()

# -----------------------------
# API функції
# -----------------------------
async def fetch_json(url):
    async with ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def get_quote():
    try:
        data = await fetch_json("https://api.quotable.io/random")
        return f"{data['content']}\n— {data['author']}"
    except:
        return "Не вдалося отримати цитату."

# Мапа погодних кодів у емодзі
WEATHER_EMOJI = {
    0: "☀️ Ясно",
    1: "🌤️ Переважно ясно",
    2: "⛅ Мінлива хмарність",
    3: "☁️ Хмарно",
    45: "🌫️ Туман",
    48: "🌫️ Іній",
    51: "🌦️ Легкий дощ",
    61: "🌧️ Дощ",
    63: "🌧️ Сильний дощ",
    71: "🌨️ Сніг",
    80: "🌦️ Зливи",
    95: "⛈️ Гроза",
}

async def get_weather(coords):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true"
        )
        data = await fetch_json(url)
        weather = data["current_weather"]
        temp = weather["temperature"]
        wind = weather["windspeed"]
        code = weather.get("weathercode", 0)
        emoji = WEATHER_EMOJI.get(code, "🌍")

        return f"{emoji}\nТемпература: {temp}°C\nВітер: {wind} км/год"
    except Exception as e:
        print("Weather error:", e)
        return "Не вдалося отримати погоду."

def find_coords(city_name):
    for region, cities in CITIES_BY_REGION.items():
        if city_name in cities:
            return cities[city_name]
    return None

# -----------------------------
# Команди
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🎲 Випадкова фраза", callback_data="random_phrase"),
            InlineKeyboardButton("🧠 Цитата", callback_data="random_quote"),
        ],
        [InlineKeyboardButton("🌦️ Погода", callback_data="choose_region")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привіт! 👋\nЯ твій Daily Helper бот.\nОберіть дію:",
        reply_markup=reply_markup
    )

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await get_quote()
    await update.message.reply_text(text)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    if data == "random_phrase":
        phrase = meme_bot.get_random_phrase()
        await query.message.reply_text(phrase)

    elif data == "random_quote":
        text = await get_quote()
        await query.message.reply_text(text)

    elif data == "choose_region":
        keyboard = [[InlineKeyboardButton(region, callback_data=f"region_{region}")]
                    for region in sorted(CITIES_BY_REGION.keys())]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Оберіть область:", reply_markup=reply_markup)

    elif data.startswith("region_"):
        region = data.replace("region_", "")
        cities = CITIES_BY_REGION[region]
        keyboard, row = [], []
        for i, city in enumerate(sorted(cities.keys()), 1):
            row.append(InlineKeyboardButton(city, callback_data=f"city_{city}"))
            if i % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(f"Оберіть місто в {region}:", reply_markup=reply_markup)

    elif data.startswith("city_"):
        city = data.replace("city_", "")
        USER_CITY[chat_id] = city
        coords = find_coords(city)
        if coords:
            weather_info = await get_weather(coords)
            await query.message.reply_text(f"Місто встановлено: {city}\n\nПоточна погода:\n{weather_info}")
        else:
            await query.message.reply_text(f"Місто встановлено: {city}\nПогода недоступна.")

# -----------------------------
# Ранкові повідомлення
# -----------------------------
async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, city in USER_CITY.items():
        quote_text = await get_quote()
        coords = find_coords(city)
        weather_text = await get_weather(coords) if coords else "Погода недоступна."
        await context.bot.send_message(
            chat_id,
            f"Доброго ранку! ☕\n\n{quote_text}\n\nПогода у {city}:\n{weather_text}"
        )

# -----------------------------
# Запуск бота
# -----------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    app.job_queue.run_daily(daily_job, time=dt_time(hour=8, minute=0))

    print("Бот запущено...")
    app.run_polling()
