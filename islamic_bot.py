import os
import json
import random
import logging
import pytz

from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==================================================
# SETTINGS
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

DHAKA = pytz.timezone("Asia/Dhaka")

CHAT_FILE = "chats.json"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ==================================================
# LOAD / SAVE CHAT IDS
# ==================================================

def load_chats():
    try:
        if os.path.exists(CHAT_FILE):
            with open(CHAT_FILE, "r") as f:
                return set(json.load(f))
    except:
        pass

    return set()


def save_chats():
    with open(CHAT_FILE, "w") as f:
        json.dump(list(active_chats), f)


active_chats = load_chats()

# ==================================================
# MESSAGES
# ==================================================

PRAYER_MESSAGES = {
    "fajr": [
        "🌅 ফজরের সময় হয়েছে!\n🕌 নামাজ পড়ুন ভাই!",
        "⭐ উঠুন! ফজরের আযান হয়েছে!"
    ],

    "dhuhr": [
        "☀️ যোহরের সময় হয়েছে!\n🕌 নামাজ পড়ুন!",
        "🌞 কাজ থামান, যোহর পড়ুন!"
    ],

    "asr": [
        "🌤️ আসরের সময় হয়েছে!",
        "⭐ আসরের নামাজ পড়ুন!"
    ],

    "maghrib": [
        "🌇 মাগরিবের আযান হয়েছে!",
        "🌆 দ্রুত মাগরিব পড়ুন!"
    ],

    "isha": [
        "🌙 ইশার সময় হয়েছে!",
        "⭐ ইশার নামাজ পড়ুন!"
    ]
}

HOURLY = [
    "⏰ নতুন ঘন্টা শুরু!\n💪 কাজ চালিয়ে যান!",
    "🚀 YouTube এ সফল হতে কাজ করুন!",
    "🎬 আজকের ভিডিও শেষ করেছেন?"
]

# ==================================================
# PRAYER TIMES
# ==================================================

def get_prayer_times():

    return {
        "fajr": (4, 15),
        "dhuhr": (12, 0),
        "asr": (15, 45),
        "maghrib": (18, 30),
        "isha": (19, 45),
    }

# ==================================================
# SEND MESSAGE TO ALL GROUPS
# ==================================================

async def broadcast(app, text):

    remove_list = []

    for chat_id in active_chats:

        try:
            await app.bot.send_message(
                chat_id=chat_id,
                text=text
            )

        except Exception as e:

            logger.error(f"Failed {chat_id}: {e}")

            remove_list.append(chat_id)

    for r in remove_list:
        active_chats.discard(r)

    save_chats()

# ==================================================
# CHECK PRAYER TIMES
# ==================================================

async def prayer_loop(context: ContextTypes.DEFAULT_TYPE):

    now = datetime.now(DHAKA)

    h = now.hour
    m = now.minute

    prayers = get_prayer_times()

    for prayer, (ph, pm) in prayers.items():

        if h == ph and m == pm:

            msg = random.choice(
                PRAYER_MESSAGES[prayer]
            )

            msg += f"\n\n🕐 {now.strftime('%I:%M %p')}"

            await broadcast(context.application, msg)

# ==================================================
# HOURLY MOTIVATION
# ==================================================

async def hourly_loop(context: ContextTypes.DEFAULT_TYPE):

    now = datetime.now(DHAKA)

    if now.minute != 0:
        return

    if now.hour < 4:
        return

    msg = random.choice(HOURLY)

    msg += f"\n\n🕐 {now.strftime('%I:%M %p')}"

    await broadcast(context.application, msg)

# ==================================================
# TRACK CHATS
# ==================================================

async def track_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.effective_chat:
        return

    chat_id = update.effective_chat.id

    if chat_id not in active_chats:

        active_chats.add(chat_id)

        save_chats()

        logger.info(f"New Chat Saved: {chat_id}")

# ==================================================
# START COMMAND
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    active_chats.add(chat_id)

    save_chats()

    await update.message.reply_text(
        "🕌 Islamic Reminder Bot Active!\n\n"
        "✅ নামাজ Reminder\n"
        "✅ Hourly Motivation\n"
        "✅ Auto Working"
    )

# ==================================================
# MAIN
# ==================================================

def main():

    if not BOT_TOKEN:
        print("BOT_TOKEN NOT FOUND")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # COMMANDS
    app.add_handler(
        CommandHandler("start", start)
    )

    # TRACK ALL MESSAGES
    app.add_handler(
        MessageHandler(
            filters.ALL,
            track_chat
        )
    )

    # JOBS
    app.job_queue.run_repeating(
        prayer_loop,
        interval=60,
        first=5
    )

    app.job_queue.run_repeating(
        hourly_loop,
        interval=60,
        first=10
    )

    print("🕌 BOT RUNNING...")

    app.run_polling()

# ==================================================

if __name__ == "__main__":
    main()
