import os
import re
import sqlite3
import requests
import torch
import logging
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
#from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '59'
ALLOWED_CHAT_IDS = [-108]  # Replace with the allowed chat IDs
OPENWEATHERMAP_API_KEY = '59'

#from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
#tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
#model = AutoModelForSeq2SeqLM.from_pretrained("facebook/blenderbot-400M-distill")

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-1B-distill")

model = AutoModelForSeq2SeqLM.from_pretrained("facebook/blenderbot-1B-distill")

# Set up SQLite database
def setup_database():
    conn = sqlite3.connect("memory.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS memory
                   (id INTEGER PRIMARY KEY,
                    keyword TEXT UNIQUE,
                    value TEXT)''')



    conn.commit()
    return conn

conn = setup_database()
memory = {}

def setup_database2():
    conn = sqlite3.connect("chatmemory.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS conversation_history
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    message TEXT)''')
    conn.commit()
    return conn

conn = setup_database2()

def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in ALLOWED_CHAT_IDS:
        return

    update.message.reply_text("Hi! I'm a self-training Telegram bot. You can talk to me or ask me to remember something for you.")

def save_conversation_history(chat_id: int, message: str):
#    global conn
#    cur = conn.cursor()
#    cur.execute("INSERT INTO conversation_history (chat_id, message) VALUES (?, ?)", (chat_id, message))
#    conn.commit()
    local_conn = sqlite3.connect("chatmemory.db")
    cur = local_conn.cursor()
    cur.execute("INSERT INTO conversation_history (chat_id, message) VALUES (?, ?)", (chat_id, message))
    local_conn.commit()
    local_conn.close()

def get_conversation_history(chat_id: int):
    # Use a local connection instead of the global one
    local_conn = sqlite3.connect("chatmemory.db")
    cur = local_conn.cursor()
    cur.execute("SELECT message FROM conversation_history WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
    results = cur.fetchall()
    local_conn.close()
    return [result[0] for result in results]

#def get_conversation_history(chat_id: int):
#    global conn
#    cur = conn.cursor()
#    cur.execute("SELECT message FROM conversation_history WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
#    results = cur.fetchall()
#    return [result[0] for result in results]

def handle_message(update: Update, context: CallbackContext):
    global conn
    input_text = update.message.text.lower()
    chat_id = update.message.chat_id

    if chat_id not in ALLOWED_CHAT_IDS:
        return

    wake_word = "jbot"
    if wake_word.lower() not in input_text:
        return

    if input_text.startswith("remember "):
        keyword, text_to_remember = input_text[9:].split(" ", 1)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO memory (keyword, value) VALUES (?, ?)", (keyword, text_to_remember))
        conn.commit()
        update.message.reply_text(f"I have saved the text under the keyword '{keyword}'.")
        save_conversation_history(chat_id, input_text)
    elif input_text.startswith("recall "):
        keyword = input_text[7:].strip()
        cur = conn.cursor()
        cur.execute("SELECT value FROM memory WHERE keyword=?", (keyword,))
        result = cur.fetchone()
        save_conversation_history(chat_id, input_text)
        if result:
            text = result[0]
            update.message.reply_text(f"Text under the keyword '{keyword}':\n{text}")
            save_conversation_history(chat_id, f"Text under the keyword '{keyword}':\n{text}")
        else:
            update.message.reply_text(f"I don't have any text saved under the keyword '{keyword}'.")
            save_conversation_history(chat_id, f"I don't have any text saved under the keyword '{keyword}'.")
    else:
        save_conversation_history(chat_id, input_text)
#        response = generate_response(chat_id, update.message.text)
        response = generate_response(chat_id, update.message.text.replace(wake_word, '', 1).strip())

        # Save user input and bot response to a file
        with open("training_data.txt", "a") as f:
            f.write(f"{input_text}\n{response}\n")

        update.message.reply_text(response)
        save_conversation_history(chat_id, response)

def generate_response(chat_id: int, input_text: str):
    # Get the conversation history for the chat_id
    conversation_history = get_conversation_history(chat_id)

    max_input_length = 128  # This can be any value less than the maximum position embeddings

    # Concatenate the conversation history with the new input_text
    full_input = " ".join(conversation_history) + input_text

    # Limit the full_input to a certain length
    full_input = full_input[:max_input_length]

    input_ids = tokenizer.encode(full_input, return_tensors='pt')
    attention_mask = torch.ones(input_ids.shape, dtype=torch.long, device=model.device)
    pad_token_id = tokenizer.eos_token_id
    output = model.generate(input_ids, max_length=50, num_return_sequences=1, no_repeat_ngram_size=2, early_stopping=True)
    response = tokenizer.decode(output[0], skip_special_tokens=True)

    # Save the response to the conversation history
    save_conversation_history(chat_id, response)

    return response

def remember(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in ALLOWED_CHAT_IDS:
        return

    if len(context.args) < 2:
        update.message.reply_text("Please provide a keyword and the text to remember.")
        return

    keyword = context.args[0]
    text_to_remember = ' '.join(context.args[1:])

    conn = sqlite3.connect('memory.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO memory (keyword, value) VALUES (?, ?)", (keyword, text_to_remember))
    conn.commit()
    conn.close()

    update.message.reply_text(f"I have saved the text under the keyword '{keyword}'.")

def recall(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in ALLOWED_CHAT_IDS:
        return

    if not context.args:
        update.message.reply_text("Please provide a keyword to recall the text.")
        return

    keyword = context.args[0]

    conn = sqlite3.connect('memory.db')
    c = conn.cursor()
    c.execute("SELECT value FROM memory WHERE keyword=?", (keyword,))
    result = c.fetchone()
    conn.close()

    if result:
        text = result[0]
        update.message.reply_text(f"Text under the keyword '{keyword}':\n{text}")
    else:
        update.message.reply_text(f"I don't have any text saved under the keyword '{keyword}'.")

import datetime

def get_weather(city: str) -> str:
    # Get the current weather
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=imperial'
    response = requests.get(url)
    data = response.json()

    if data.get('cod') != 200:
        return f"Sorry, I couldn't find the weather for {city}."

    current_weather = data['weather'][0]['description']
    current_temp = data['main']['temp']
    temp_min = data['main']['temp_min']
    temp_max = data['main']['temp_max']

    # Get the 5-day forecast
    forecast_url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=imperial'
    forecast_response = requests.get(forecast_url)
    forecast_data = forecast_response.json()

    if forecast_data.get('cod') != "200":
        return f"Sorry, I couldn't find the 5-day forecast for {city}."

    forecast_list = forecast_data['list']
    daily_forecasts = {}
    for forecast in forecast_list:
        dt = datetime.datetime.fromtimestamp(forecast['dt'])
        date = dt.date()
        if date not in daily_forecasts:
            daily_forecasts[date] = {
                'min_temp': forecast['main']['temp_min'],
                'max_temp': forecast['main']['temp_max'],
                'weather': forecast['weather'][0]['description']
            }
        else:
            daily_forecasts[date]['min_temp'] = min(daily_forecasts[date]['min_temp'], forecast['main']['temp_min'])
            daily_forecasts[date]['max_temp'] = max(daily_forecasts[date]['max_temp'], forecast['main']['temp_max'])

    # Format the output
    result = f'The current weather in {city} is {current_weather} with a temperature of {current_temp}°F (low: {temp_min}°F, high: {temp_max}°F).\n\n5-day forecast:\n'
    for date, daily_forecast in daily_forecasts.items():
        result += f"{date.strftime('%A, %B %d')}: {daily_forecast['weather']} (low: {daily_forecast['min_temp']}°F, high: {daily_forecast['max_temp']}°F)\n"

    return result.strip()


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


def send_weather_updates(updater: Updater, chat_id: int):
    if chat_id not in ALLOWED_CHAT_IDS:
        return

    city = 'West Caldwell'  # Replace with the city you want to get updates for
    weather_info = get_weather(city)
    updater.bot.send_message(chat_id=chat_id, text=weather_info)

def schedule_weather_updates(updater: Updater):
    scheduler = BackgroundScheduler()
    times = ['07:30', '11:45', '17:00']  # Update these to the times you want weather updates

    for chat_id in ALLOWED_CHAT_IDS:
        for time in times:
            hour, minute = map(int, time.split(':'))
            scheduler.add_job(
                send_weather_updates,
                'cron',
                args=[updater, chat_id],  # Pass the updater and chat_id as arguments
                hour=hour,
                minute=minute,
                timezone='UTC'  # Update this to your desired timezone
            )

    scheduler.start()



def main():
    # Replace 'YOUR_API_TOKEN' with your Telegram bot's API token
    updater = Updater(TOKEN)
    schedule_weather_updates(updater)
    conn = setup_database()
    conn = setup_database2()
    dp = updater.dispatcher

    # Add command and message handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler('weather', weather))
    dp.add_handler(CommandHandler("remember", remember, pass_args=True))
    dp.add_handler(CommandHandler("recall", recall, pass_args=True))
    dp.add_handler(MessageHandler(Filters.regex(r'(?i)remember .*') & ~Filters.command, remember))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command & Filters.chat_type.groups, handle_message))

    # Start the bot
    updater.start_polling()

    # Run the bot until Ctrl-C is pressed or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
