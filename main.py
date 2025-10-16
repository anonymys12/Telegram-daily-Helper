import os
import random
from datetime import time as dt_time
from aiohttp import ClientSession
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.request import HTTPXRequest

from cities_by_region import CITIES_BY_REGION  # словник областей та міст

# -----------------------------
# Завантаження токена
# -----------------------------
load_dotenv(dotenv_path=".env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не знайдено! Перевір .env файл.")

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
# Запит до API
# -----------------------------
async def fetch_json(url):
    async with ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def get_quote():
    return meme_bot.get_random_phrase()

# -----------------------------
# Погода
# -----------------------------
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

async def get_weather(coords, days=7):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={coords['lat']}&longitude={coords['lon']}"
            f"&current_weather=true&daily=temperature_2m_max,temperature_2m_min,"
            f"precipitation_sum,windspeed_10m_max,sunrise,sunset,weathercode&timezone=Europe/Kiev"
        )
        data = await fetch_json(url)

        # --- Функції для емодзі ---
        def temp_emoji(temp):
            if temp <= 0: return "❄️"
            elif temp <= 10: return "🧥"
            elif temp <= 20: return "🌤️"
            elif temp <= 30: return "🌞"
            else: return "🔥"

        def wind_emoji(speed):
            if speed < 5: return "🍃"
            elif speed < 15: return "💨"
            else: return "🌪️"

        def rain_emoji(precip):
            if precip == 0: return "💦"
            elif precip < 5: return "🌦️"
            elif precip < 20: return "🌧️"
            else: return "⛈️"

        # Поточна погода
        current = data.get("current_weather", {})
        temp = current.get("temperature", "N/A")
        wind = current.get("windspeed", "N/A")
        code = current.get("weathercode", 0)
        emoji = WEATHER_EMOJI.get(code, "🌍")
        current_weather = (
            f"🌟 *Поточна погода*\n"
            f"{emoji} {temp_emoji(temp)}\n"
            f"🌡 *Температура:* {temp}°C\n"
            f"💨 *Вітер:* {wind} км/год {wind_emoji(wind)}\n"
            f"——————————————\n"
        )

        # Прогноз на N днів у вигляді карток
        daily = data.get("daily", {})
        forecast = f"🌈 *Прогноз на {days} днів:*\n"
        for i in range(min(days, len(daily.get("time", [])))):
            code = daily.get("weathercode", [0]*days)[i]
            day_emoji = WEATHER_EMOJI.get(code, "🌍")
            t_min = daily['temperature_2m_min'][i]
            t_max = daily['temperature_2m_max'][i]
            precip = daily['precipitation_sum'][i]
            wind_speed = daily['windspeed_10m_max'][i]

            forecast += (
                f"📅 *{daily['time'][i]}* {day_emoji} {temp_emoji((t_min+t_max)/2)}\n"
                f"🌡 *Температура:* {t_min}°C – {t_max}°C\n"
                f"💧 *Опади:* {precip} мм {rain_emoji(precip)}\n"
                f"💨 *Вітер:* {wind_speed} км/год {wind_emoji(wind_speed)}\n"
                f"☀️ *Схід:* {daily['sunrise'][i].split('T')[1]} | 🌙 *Захід:* {daily['sunset'][i].split('T')[1]}\n"
                f"——————————————\n"
            )
        return current_weather + forecast
    except Exception as e:
        print("Weather error:", e)
        return "Не вдалося отримати погоду."

def find_coords(city_name):
    for region, cities in CITIES_BY_REGION.items():
        if city_name in cities:
            return cities[city_name]
    return None

# -----------------------------
# Команди бота
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

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    if data == "random_phrase":
        await query.message.reply_text(meme_bot.get_random_phrase())

    elif data == "random_quote":
        await query.message.reply_text(await get_quote())

    elif data == "choose_region":
        keyboard = [[InlineKeyboardButton(region, callback_data=f"region_{region}")]
                    for region in sorted(CITIES_BY_REGION.keys())]
        await query.message.reply_text("Оберіть область:", reply_markup=InlineKeyboardMarkup(keyboard))

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
        await query.message.reply_text(f"Оберіть місто в {region}:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("city_"):
        city = data.replace("city_", "")
        USER_CITY[chat_id] = city
        coords = find_coords(city)
        if coords:
            keyboard = [
                [InlineKeyboardButton("3 дні", callback_data=f"weather_{city}_3")],
                [InlineKeyboardButton("5 днів", callback_data=f"weather_{city}_5")],
                [InlineKeyboardButton("7 днів", callback_data=f"weather_{city}_7")]
            ]
            await query.message.reply_text(
                f"Місто встановлено: {city}\nОберіть тривалість прогнозу:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.message.reply_text(f"Місто встановлено: {city}\nПогода недоступна.")

    elif data.startswith("weather_"):
        _, city, days = data.split("_")
        coords = find_coords(city)
        if coords:
            weather_info = await get_weather(coords, int(days))
            await query.message.reply_text(
                f"Прогноз для {city} на {days} днів:\n\n{weather_info}",
                parse_mode="Markdown"
            )

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
            f"Доброго ранку! ☕\n\n{quote_text}\n\n{weather_text}",
            parse_mode="Markdown"
        )

# -----------------------------
# Запуск бота
# -----------------------------
if __name__ == "__main__":
    request = HTTPXRequest()  # без keepalive_expiry
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    if app.job_queue:
        app.job_queue.run_daily(daily_job, time=dt_time(hour=8, minute=0))
    else:
        print("⚠️ JobQueue не активна — щоденне повідомлення вимкнено.")

    print("✅ Бот запущено...")
    app.run_polling(stop_signals=None)
