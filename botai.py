import os
import re
import sqlite3
import logging
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
#from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load GPT-2 model and tokenizer
#model = GPT2LMHeadModel.from_pretrained("gpt2")
#tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
#from transformers import AutoTokenizer, AutoModelForCausalLM
#tokenizer = AutoTokenizer.from_pretrained("Nicki/gpt3-base")
#model = AutoModelForCausalLM.from_pretrained("Nicki/gpt3-base")

#from transformers import AutoTokenizer, AutoModelForCausalLM
#tokenizer = AutoTokenizer.from_pretrained("ingen51/DialoGPT-medium-GPT4")
#model = AutoModelForCausalLM.from_pretrained("ingen51/DialoGPT-medium-GPT4")

from transformers import AutoTokenizer, AutoModelForCausalLM
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-large")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-large")

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

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hi! I'm a self-training Telegram bot. You can talk to me or ask me to remember something for you.")

def handle_message(update: Update, context: CallbackContext):
    global conn
    input_text = update.message.text.lower()

    if input_text.startswith("what did i"):
        key = input_text[10:].strip()
        cur = conn.cursor()
        cur.execute("SELECT value FROM memory WHERE key LIKE ?", ('%' + key + '%',))
        result = cur.fetchone()
        if result:
            update.message.reply_text(f"You said: {result[0]}")
        else:
            update.message.reply_text(f"Sorry, I don't remember {key}.")
        return

    response = generate_response(update.message.text)

    # Save user input and bot response to a file
    with open("training_data.txt", "a") as f:
        f.write(f"{input_text}\n{response}\n")

    update.message.reply_text(response)

def generate_response(input_text: str):
    input_ids = tokenizer.encode(input_text, return_tensors='pt')
    output = model.generate(input_ids, max_length=50, num_return_sequences=1, no_repeat_ngram_size=2, early_stopping=True)
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    return response

def remember(update: Update, context: CallbackContext):
    global conn
    input_text = update.message.text.lower()

    pattern = r"remember (that|) (i|) (.*?)$"
    match = re.search(pattern, input_text)
    if match:
        key = " ".join([match.group(1), match.group(2), match.group(3)]).strip()
        cur = conn.cursor()
        cur.execute("INSERT INTO memory (key, value) VALUES (?, ?)", (key, input_text))
        conn.commit()
        update.message.reply_text(f"I'll remember {input_text}.")
    else:
        update.message.reply_text("Sorry, I couldn't understand your request. Please use the format 'remember [your message]'.")

def generate_chart(update: Update, context: CallbackContext):
    global conn
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM memory")
    results = cur.fetchall()

    keys = [x[0] for x in results]
    values = [x[1] for x in results]

    plt.barh(keys, values)
    plt.xlabel('Keys')
    plt.ylabel('Values')
    plt.title('Memory Chart')
    plt.tight_layout()

    chart_path = "memory_chart.png"
    plt.savefig(chart_path)
    plt.clf()

    update.message.reply_photo(open(chart_path, "rb"))

def main():
    # Replace 'YOUR_API_TOKEN' with your Telegram bot's API token
    updater = Updater("YOUR_API_TOKEN", use_context=True)

    dp = updater.dispatcher

    # Add command and message handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("chart", generate_chart))
    dp.add_handler(MessageHandler(Filters.regex(r'(?i)remember .*') & ~Filters.command, remember))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the bot
    updater.start_polling()

    # Run the bot until Ctrl-C is pressed or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
