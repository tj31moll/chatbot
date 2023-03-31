import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Replace with your Telegram bot token
TELEGRAM_BOT_TOKEN = 'your_telegram_bot_token'
# Replace with your OpenWeatherMap API key
OPENWEATHERMAP_API_KEY = 'your_openweathermap_api_key'

ALLOWED_CHAT_IDS = [123456789, 987654321]  # Replace with the allowed chat IDs

def get_weather(city: str) -> str:
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric'
    response = requests.get(url)
    data = response.json()

    if data.get('cod') == 200:
        weather = data['weather'][0]['description']
        temp = data['main']['temp']
        return f'The weather in {city} is {weather} with a temperature of {temp}°C.'
    else:
        return f"Sorry, I couldn't find the weather for {city}."

def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in ALLOWED_CHAT_IDS:
        return
    update.message.reply_text('Hi! Type /weather followed by a city name to get the current weather.')

def weather(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in ALLOWED_CHAT_IDS:
        return

    if not context.args:
        update.message.reply_text('Please provide a city name.')
    else:
        city = ' '.join(context.args)
        weather_info = get_weather(city)
        update.message.reply_text(weather_info)

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('weather', weather))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
