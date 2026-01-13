import telebot
import os
import time
import random
import string

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
BOT_USERNAME = os.getenv("BOT_USERNAME")  # without @

bot = telebot.TeleBot(BOT_TOKEN)

USERS_FILE = "users.txt"
REFERRALS_FILE = "referrals.txt"
PROFILES_FILE = "profiles.txt"

# ================= USER STORAGE =================

def save_user(user_id):
    if not os.path.exists(USERS_FILE):
        open(USERS_FILE, "w").close()

    with open(USERS_FILE, "r+") as f:
        users = set(f.read().splitlines())
        if str(user_id) not in users:
            f.write(f"{user_id}\n")

# ================= REFERRAL SYSTEM =================

def save_referral(referrer_id, new_user_id):
    if not os.path.exists(REFERRALS_FILE):
        open(REFERRALS_FILE, "w").close()

    with open(REFERRALS_FILE, "r+") as f:
        lines = f.read().splitlines()

        # Prevent duplicate or inherited referrals
        for line in lines:
            if line.endswith(f":{new_user_id}"):
                return False

        f.write(f"{referrer_id}:{new_user_id}\n")
        return True


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
    else:
        return 0

# ================= LICENSE SYSTEM =================

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

# ================= START COMMAND =================

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    save_user(user_id)

    # Handle referral
    parts = message.text.split()
    if len(parts) > 1:
        referrer_id = parts[1]

        if referrer_id.isdigit():
            referrer_id = int(referrer_id)
            if referrer_id != user_id:
                success = save_referral(referrer_id, user_id)
                if success:
                    bot.send_message(
                        referrer_id,
                        "🎉 New referral joined using your link!\n"
                        "Your referral count has been updated."
                    )

    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    bot.send_message(
        user_id,
        "Welcome to AI Crypto Software 👋\n\n"
        "This is the official AI Crypto Software Telegram bot.\n\n"
        "Here you will receive:\n"
        "• Important announcements\n"
        "• Software updates\n"
        "• Official notices\n\n"
        "🎁 Referral Program\n"
        "Invite users using your referral link and earn 5–10% discount.\n\n"
        f"🔗 Your referral link:\n{referral_link}\n\n"
        "You may also ask your questions or FAQs here.\n\n"
        "Thank you for being part of AI Crypto."
    )

# ================= PROFILE =================

@bot.message_handler(commands=["profile"])
def profile(message):
    user = message.from_user
    user_id = message.chat.id

    first = user.first_name or ""
    last = user.last_name or ""
    name = (first + " " + last).strip()

    if user.username:
        display_name = f"{name} (@{user.username})"
    else:
        display_name = name

    license_key = get_or_create_license(user_id)
    referrals = get_referral_count(user_id)
    discount = get_discount_percent(user_id)
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    bot.send_message(
        user_id,
        f"👤 Profile — {display_name}\n\n"
        f"🔑 License Key:\n||{license_key}||\n\n"
        f"👥 Referrals: {referrals}\n"
        f"💸 Discount: {discount}%\n\n"
        f"🔗 Personal Referral Link:\n{referral_link}",
        parse_mode="MarkdownV2"
    )


# ================= USER COMMAND =================

@bot.message_handler(commands=["myreferrals"])
def my_referrals(message):
    count = get_referral_count(message.chat.id)
    discount = get_discount_percent(message.chat.id)

    bot.reply_to(
        message,
        f"👥 Referrals: {count}\n"
        f"💸 Discount: {discount}%"
    )

# ================= ADMIN COMMANDS =================

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
                bot.send_photo(
                    user,
                    reply.photo[-1].file_id,
                    caption=reply.caption or ""
                )
            elif reply.text:
                bot.send_message(user, reply.text)

            sent += 1
            time.sleep(0.05)
        except:
            pass

    bot.reply_to(message, f"📢 Broadcast sent to {sent} users.")


@bot.message_handler(commands=["reply"])
def reply_to_user(message):
    if message.chat.id != OWNER_ID:
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Usage:\n/reply USER_ID message")
        return

    user_id = parts[1]
    reply_text = parts[2]

    try:
        bot.send_message(user_id, reply_text)
        bot.reply_to(message, "✅ Reply sent.")
    except:
        bot.reply_to(message, "❌ Failed.")


@bot.message_handler(commands=["referrals"])
def referrals_stats(message):
    if message.chat.id != OWNER_ID:
        return

    if not os.path.exists(REFERRALS_FILE):
        bot.reply_to(message, "No referrals yet.")
        return

    stats = {}
    with open(REFERRALS_FILE, "r") as f:
        for line in f:
            ref, _ = line.strip().split(":", 1)
            stats[ref] = stats.get(ref, 0) + 1

    response = "📊 Referral Stats\n\n"
    for user, count in stats.items():
        discount = get_discount_percent(int(user))
        response += f"User {user} → {count} referrals → {discount}%\n"

    bot.reply_to(message, response)

# ================= FORWARD USER MESSAGES =================

@bot.message_handler(func=lambda message: message.text and not message.text.startswith("/"))
def forward_user_message(message):
    if message.chat.id == OWNER_ID:
        return

    save_user(message.chat.id)

    bot.send_message(
        OWNER_ID,
        "📩 New user message\n\n"
        f"User ID: {message.chat.id}\n"
        f"Message:\n{message.text}"
    )

# ================= START BOT =================

bot.infinity_polling()
