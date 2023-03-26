import logging
import random
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Load GPT-2 model and tokenizer
model = GPT2LMHeadModel.from_pretrained("gpt2")
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# Your Telegram bot token
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hi! I'm a self-training Telegram bot. Send me a message, and I'll try to respond!")

def generate_response(input_text):
    input_ids = tokenizer.encode(input_text, return_tensors='pt')
    response_ids = model.generate(input_ids, max_length=100, num_return_sequences=1)
    response = tokenizer.decode(response_ids[0], skip_special_tokens=True)
    return response

def handle_message(update: Update, context: CallbackContext):
    input_text = update.message.text
    response = generate_response(input_text)
    update.message.reply_text(response)

def error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
