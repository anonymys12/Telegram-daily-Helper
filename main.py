import os
import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from cities_by_region import CITIES_BY_REGION

# ----------------------
# Завантажуємо токен з .env
# ----------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ----------------------
# Команди бота
# ----------------------
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я твій Daily Helper бот.\n\n"
        "Доступні команди:\n"
        "/weather - погода за містами України\n"
        "/quote - випадкова цитата"
    )

async def quote(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get("https://api.quotable.io/random")
        data = res.json()
        await update.message.reply_text(f"{data['content']}\n— {data['author']}")
    except Exception:
        await update.message.reply_text("Не вдалося отримати цитату.")

# ----------------------
# Weather з кнопками
# ----------------------
async def weather(update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(region, callback_data=f"region_{region}")]
        for region in sorted(CITIES_BY_REGION.keys())
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оберіть область:", reply_markup=reply_markup)

async def button(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("region_"):
        region = data.replace("region_", "")
        cities = CITIES_BY_REGION[region]
        keyboard = []
        row = []
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
        for region, cities in CITIES_BY_REGION.items():
            if city in cities:
                coords = cities[city]
                weather_info = get_weather(coords)
                await query.message.reply_text(f"Погода в {city}:\n{weather_info}")

def get_weather(coords):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true"
        res = requests.get(url).json()
        temp = res["current_weather"]["temperature"]
        wind = res["current_weather"]["windspeed"]
        return f"Температура: {temp}°C\nВітер: {wind} км/год"
    except:
        return "Не вдалося отримати погоду."

# ----------------------
# Основна функція
# ----------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quote", quote))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CallbackQueryHandler(button))
    print("Бот запущено...")
    app.run_polling()

if __name__ == "__main__":
    main()
