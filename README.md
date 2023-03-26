# Self-Training Telegram Bot

This is a self-training Telegram bot that can engage in conversations and remember information using a simple memory feature. The bot is built using Python, the `python-telegram-bot` library, and the GPT-2 model from the `transformers` library. The memory feature uses SQLite to store information persistently.

## Features

- Engage in conversations using the GPT-2 model
- Remember information provided by users
- Retrieve remembered information
- Display a chart of remembered information

## Requirements

- Python 3.7 or later
- python-telegram-bot
- transformers
- sqlite3
- matplotlib

## Installation

1. Clone the repository:

apt update && apt install nano sudo git python3 python3-pip
git clone https://github.com/your-username/self-training-telegram-bot.git

csharp


2. Change into the project directory:

apt update && apt install nano sudo git python3 python3-pip
cd self-training-telegram-bot
pip install python-telegram-bot==13.7 
transformers==4.11.3 
python3 -m venv my_bot_env 
source my_bot_env/bin/activate


3. Set up a virtual environment (optional but recommended):

python3 -m venv venv
source venv/bin/activate

markdown


4. Install the required packages:

pip install -r requirements.txt

css


5. Add your Telegram bot API token to the `self_training_telegram_bot.py` script:

updater = Updater("YOUR_API_TOKEN", use_context=True)

Replace YOUR_API_TOKEN with your actual Telegram bot API token.
Usage

    Start the bot by running:

python self_training_telegram_bot.py

    In Telegram, find your bot by its username and start a conversation.

    Talk to the bot, ask it to remember something, or ask about something it remembered.

    Use the /chart command to get a chart of the stored data.
