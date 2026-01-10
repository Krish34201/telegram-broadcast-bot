import telebot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
USERS_FILE = "users.txt"


def save_user(user_id):
    with open(USERS_FILE, "a+") as f:
        f.seek(0)
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(f"{user_id}\n")


# START COMMAND
@bot.message_handler(commands=["start"])
def start(message):
    save_user(message.chat.id)
    bot.send_message(
        message.chat.id,
        "Welcome to AI Crypto Software 👋\n\n"
        "This is the official AI Crypto Software Telegram bot.\n\n"
        "Here you will receive:\n"
        "• Important announcements\n"
        "• Software updates\n"
        "• Official notices\n\n"
        "You may also ask your questions or FAQs here.\n\n"
        "Thank you for being part of AI Crypto."
    )



# BROADCAST (OWNER ONLY)
@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if message.chat.id != OWNER_ID:
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(message, "Usage:\n/broadcast Your message here")
        return

    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()

    sent = 0
    for user in users:
        try:
            bot.send_message(user, text)
            sent += 1
        except:
            pass

    bot.reply_to(message, f"Broadcast sent to {sent} users.")


# FORWARD USER MESSAGES TO OWNER
@bot.message_handler(func=lambda message: True)
def forward_user_message(message):
    if message.chat.id == OWNER_ID:
        return

    save_user(message.chat.id)

    text = (
        "📩 New user message\n\n"
        f"User ID: {message.chat.id}\n"
        f"Message:\n{message.text}"
    )
    bot.send_message(OWNER_ID, text)


# OWNER REPLY COMMAND
@bot.message_handler(commands=["reply"])
def reply_to_user(message):
    if message.chat.id != OWNER_ID:
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Usage:\n/reply USER_ID your message")
        return

    user_id = parts[1]
    reply_text = parts[2]

    try:
        bot.send_message(user_id, reply_text)
        bot.reply_to(message, "✅ Reply sent successfully.")
    except:
        bot.reply_to(message, "❌ Failed to send reply. Check USER_ID.")


bot.infinity_polling()
