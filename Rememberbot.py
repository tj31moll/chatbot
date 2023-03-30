import logging

from telegram import Update, ForceReply

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging

logging.basicConfig(

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO

)

logger = logging.getLogger(__name__)

# Your bot token obtained from BotFather

TOKEN = "YOUR_TOKEN_HERE"

# Memory storage

memory = {}

# Start command

def start(update: Update, context: CallbackContext):

    update.message.reply_text(

        'Hi! I am your remember bot. To save something, use the /remember command, followed by a keyword and the text you want me to remember. To recall it, use the /recall command followed by the keyword.'

    )

# Remember command

def remember(update: Update, context: CallbackContext):

    if len(context.args) < 2:

        update.message.reply_text("Please provide a keyword and the text to remember.")

        return

    keyword = context.args[0]

    text_to_remember = ' '.join(context.args[1:])

    memory[keyword] = text_to_remember

    update.message.reply_text(f"I have saved the text under the keyword '{keyword}'.")

# Recall command

def recall(update: Update, context: CallbackContext):

    if not context.args:

        update.message.reply_text("Please provide a keyword to recall the text.")

        return

    keyword = context.args[0]

    text = memory.get(keyword)

    if text:

        update.message.reply_text(f"Text under the keyword '{keyword}':\n{text}")

    else:

        update.message.reply_text(f"I don't have any text saved under the keyword '{keyword}'.")

# Main function

def main():

    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    dispatcher.add_handler(CommandHandler("remember", remember, pass_args=True))

    dispatcher.add_handler(CommandHandler("recall", recall, pass_args=True))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':

    main()

