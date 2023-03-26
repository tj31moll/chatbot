import os

def handle_message(update: Update, context: CallbackContext):
    input_text = update.message.text
    response = generate_response(input_text)

    # Save user input and bot response to a file
    with open("training_data.txt", "a") as f:
        f.write(f"{input_text}\n{response}\n")

    update.message.reply_text(response)
