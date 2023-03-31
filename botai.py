import os
import re
import sqlite3
import requests
import torch
import logging
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
#from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "YOUR_TOKEN_HERE"
ALLOWED_CHAT_IDS = [123456789, 987654321]  # Replace with the allowed chat IDs
OPENWEATHERMAP_API_KEY = 'your_openweathermap_api_key'

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/blenderbot-400M-distill")

# Set up SQLite database
def setup_database():
    conn = sqlite3.connect("memory.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS memory
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT,
                    value TEXT)''')
    conn.commit()
    return conn

conn = setup_database()
memory = {}


def setup_database2():
    conn = sqlite3.connect("chatmemory.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS memory
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT,
                    value TEXT)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS conversation_history
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    message TEXT)''')
    conn.commit()
    return conn

def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in ALLOWED_CHAT_IDS:
        return

    update.message.reply_text("Hi! I'm a self-training Telegram bot. You can talk to me or ask me to remember something for you.")

def save_conversation_history(chat_id: int, message: str):
    global conn
    cur = conn.cursor()
    cur.execute("INSERT INTO conversation_history (chat_id, message) VALUES (?, ?)", (chat_id, message))
    conn.commit()

def get_conversation_history(chat_id: int):
    global conn
    cur = conn.cursor()
    cur.execute("SELECT message FROM conversation_history WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
    results = cur.fetchall()
    return [result[0] for result in results]

def handle_message(update: Update, context: CallbackContext):
    global conn
    input_text = update.message.text.lower()
    chat_id = update.message.chat_id

    if chat_id not in ALLOWED_CHAT_IDS:
        return

    if input_text.startswith("remember "):
        keyword, text_to_remember = input_text[9:].split(" ", 1)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)", (keyword, text_to_remember))
        conn.commit()
        update.message.reply_text(f"I have saved the text under the keyword '{keyword}'.")
        save_conversation_history(chat_id, input_text)
    elif input_text.startswith("recall "):
        keyword = input_text[7:].strip()
        cur = conn.cursor()
        cur.execute("SELECT value FROM memory WHERE key=?", (keyword,))
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
        response = generate_response(chat_id, update.message.text)

        # Save user input and bot response to a file
        with open("training_data.txt", "a") as f:
            f.write(f"{input_text}\n{response}\n")

        update.message.reply_text(response)
        save_conversation_history(chat_id, response)

def generate_response(chat_id: int, input_text: str):
    # Get the conversation history for the chat_id
    conversation_history = get_conversation_history(chat_id)

    # Concatenate the conversation history with the new input_text
    full_input = " ".join(conversation_history) + input_text

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
    c.execute("INSERT OR REPLACE INTO memory (keyword, text) VALUES (?, ?)", (keyword, text_to_remember))
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
    c.execute("SELECT text FROM memory WHERE keyword=?", (keyword,))
    result = c.fetchone()
    conn.close()

    if result:
        text = result[0]
        update.message.reply_text(f"Text under the keyword '{keyword}':\n{text}")
    else:
        update.message.reply_text(f"I don't have any text saved under the keyword '{keyword}'.")

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
    # Replace 'YOUR_API_TOKEN' with your Telegram bot's API token
    updater = Updater(TOKEN)
    conn = setup_database()
    conn = setup_database2()
    dp = updater.dispatcher

    # Add command and message handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler('weather', weather))
    dispatcher.add_handler(CommandHandler("remember", remember, pass_args=True))
    dispatcher.add_handler(CommandHandler("recall", recall, pass_args=True))
    dp.add_handler(MessageHandler(Filters.regex(r'(?i)remember .*') & ~Filters.command, remember))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command & Filters.group, handle_message))

    # Start the bot
    updater.start_polling()

    # Run the bot until Ctrl-C is pressed or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
