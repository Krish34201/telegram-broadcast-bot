import telebot
import os
import time
import random
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
BOT_USERNAME = os.getenv("BOT_USERNAME")  # without @

if not BOT_USERNAME:
    raise RuntimeError("BOT_USERNAME is not set")

bot = telebot.TeleBot(BOT_TOKEN)

USERS_FILE = "users.txt"
REFERRALS_FILE = "referrals.txt"
PROFILES_FILE = "profiles.txt"

# ================= KEYBOARD =================

def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("💳 Buy access", url="https://www.crypto-mining-software.shop")
    )
    return kb

# ================= USER STORAGE =================

def save_user(user_id):
    if not os.path.exists(USERS_FILE):
        open(USERS_FILE, "w").close()

    with open(USERS_FILE, "r+") as f:
        users = set(f.read().splitlines())
        if str(user_id) not in users:
            f.write(f"{user_id}\n")

# ================= REFERRALS =================

def save_referral(referrer_id, new_user_id):
    if not os.path.exists(REFERRALS_FILE):
        open(REFERRALS_FILE, "w").close()

    with open(REFERRALS_FILE, "r+") as f:
        lines = f.read().splitlines()
        for line in lines:
            if line.endswith(f":{new_user_id}"):
                return
        f.write(f"{referrer_id}:{new_user_id}\n")


def get_referral_count(user_id):
    if not os.path.exists(REFERRALS_FILE):
        return 0

    with open(REFERRALS_FILE, "r") as f:
        return sum(1 for line in f if line.startswith(f"{user_id}:"))


def get_discount_percent(user_id):
    count = get_referral_count(user_id)
    if count >= 8:
        return 10
    elif count >= 4:
        return 7
    elif count >= 1:
        return 5
    return 0

# ================= LICENSE =================

def generate_license_key(length=12):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def get_or_create_license(user_id):
    if not os.path.exists(PROFILES_FILE):
        open(PROFILES_FILE, "w").close()

    with open(PROFILES_FILE, "r+") as f:
        lines = f.read().splitlines()
        for line in lines:
            uid, key = line.split("|", 1)
            if uid == str(user_id):
                return key

        key = generate_license_key()
        f.write(f"{user_id}|{key}\n")
        return key

# ================= START =================

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    save_user(user_id)

    # Silent referral handling
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        referrer_id = int(parts[1])
        if referrer_id != user_id:
            save_referral(referrer_id, user_id)

    bot.send_message(
        user_id,
        "Welcome to AI Crypto Software 👋\n\n"
        "This is the official AI Crypto Software Telegram bot.\n\n"
        "Here you will receive:\n"
        "• Important announcements\n"
        "• Software updates\n"
        "• Official notices\n\n"
        "Use the buttons below to continue 👇",
        reply_markup=main_menu_keyboard()
    )

# ================= PROFILE LOGIC =================

def send_profile(user, chat_id):
    first = user.first_name or ""
    last = user.last_name or ""
    name = (first + " " + last).strip()
    display_name = f"{name} (@{user.username})" if user.username else name

    license_key = get_or_create_license(chat_id)
    referrals = get_referral_count(chat_id)
    discount = get_discount_percent(chat_id)
    referral_link = f"https://t.me/{BOT_USERNAME}?start={chat_id}"

    bot.send_message(
        chat_id,
        f"<b>👤 Profile — {display_name}</b>\n\n"
        f"🔑 <b>License Key:</b>\n"
        f"<tg-spoiler>{license_key}</tg-spoiler>\n\n"
        f"👥 <b>Referrals:</b> {referrals}\n"
        f"💸 <b>Discount:</b> {discount}%\n\n"
        f"🔗 <b>Personal Referral Link:</b>\n{referral_link}",
        parse_mode="HTML"
    )

# ================= PROFILE COMMAND =================

@bot.message_handler(commands=["profile"])
def profile_cmd(message):
    send_profile(message.from_user, message.chat.id)

# ================= PROFILE BUTTON =================

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_button(call):
    send_profile(call.from_user, call.from_user.id)
    bot.answer_callback_query(call.id)

# ================= ADMIN BROADCAST =================

@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if message.chat.id != OWNER_ID:
        return

    if not message.reply_to_message:
        bot.reply_to(message, "Reply to a text or image with /broadcast")
        return

    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()

    reply = message.reply_to_message
    sent = 0

    for user in users:
        try:
            if reply.photo:
                bot.send_photo(user, reply.photo[-1].file_id, caption=reply.caption or "")
            elif reply.text:
                bot.send_message(user, reply.text)
            sent += 1
            time.sleep(0.05)
        except:
            pass

    bot.reply_to(message, f"📢 Broadcast sent to {sent} users.")

# ================= FORWARD USER MSG =================

@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def forward_user_message(message):
    if message.chat.id == OWNER_ID:
        return

    save_user(message.chat.id)
    bot.send_message(
        OWNER_ID,
        f"📩 New user message\n\nUser ID: {message.chat.id}\nMessage:\n{message.text}"
    )

# ================= RUN =================

bot.infinity_polling()
