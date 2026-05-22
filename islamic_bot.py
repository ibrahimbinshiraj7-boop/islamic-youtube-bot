import os
import json
import logging
import random
import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DHAKA_TZ = pytz.timezone("Asia/Dhaka")
CHATS_FILE = "chats.json"
# ============================================================

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# গ্রুপ ID সেভ/লোড
# ─────────────────────────────────────────
def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_chats(chats):
    with open(CHATS_FILE, "w") as f:
        json.dump(list(chats), f)

active_chats = load_chats()

# ─────────────────────────────────────────
# নামাজের সময় (মাস অনুযায়ী ঢাকা)
# ─────────────────────────────────────────
def get_prayer_times():
    month = datetime.now(DHAKA_TZ).month
    schedule = {
        1:  {"fajr":(5,15), "dhuhr":(12,15), "asr":(15,30), "maghrib":(17,45), "isha":(19,0)},
        2:  {"fajr":(5,10), "dhuhr":(12,15), "asr":(15,40), "maghrib":(18,0),  "isha":(19,15)},
        3:  {"fajr":(4,55), "dhuhr":(12,10), "asr":(15,45), "maghrib":(18,15), "isha":(19,25)},
        4:  {"fajr":(4,35), "dhuhr":(12,5),  "asr":(15,50), "maghrib":(18,25), "isha":(19,35)},
        5:  {"fajr":(4,15), "dhuhr":(11,55), "asr":(15,55), "maghrib":(18,40), "isha":(19,50)},
        6:  {"fajr":(4,5),  "dhuhr":(11,50), "asr":(16,0),  "maghrib":(18,50), "isha":(20,0)},
        7:  {"fajr":(4,10), "dhuhr":(11,55), "asr":(16,0),  "maghrib":(18,50), "isha":(20,0)},
        8:  {"fajr":(4,25), "dhuhr":(12,0),  "asr":(15,55), "maghrib":(18,40), "isha":(19,50)},
        9:  {"fajr":(4,45), "dhuhr":(12,0),  "asr":(15,45), "maghrib":(18,20), "isha":(19,30)},
        10: {"fajr":(5,0),  "dhuhr":(12,0),  "asr":(15,30), "maghrib":(18,0),  "isha":(19,10)},
        11: {"fajr":(5,15), "dhuhr":(12,0),  "asr":(15,20), "maghrib":(17,45), "isha":(19,0)},
        12: {"fajr":(5,20), "dhuhr":(12,10), "asr":(15,20), "maghrib":(17,40), "isha":(18,55)},
    }
    return schedule.get(month, schedule[1])

# ─────────────────────────────────────────
# নামাজের মেসেজ
# ─────────────────────────────────────────
PRAYER_MESSAGES = {
    "fajr": [
        "🌅 আল্লাহু আকবার! ফজরের সময় হয়েছে!\n🕌 উঠুন, অজু করুন, নামাজ পড়ুন!\n📊 নামাজ শেষে YT Studio খুলুন — রাতের ভিউ দেখুন!\n💪 যে ফজরে ওঠে, সে জীবনে পিছিয়ে পড়ে না!",
        "🌄 সুবহানাল্লাহ! ফজরের আযান হয়েছে!\n🕌 নামাজ পড়ে দিন শুরু করুন — বরকতময় সকাল!\n🎬 নামাজের পর স্ক্রিপ্ট লিখুন — সকালের মাথা সবচেয়ে ক্রিয়েটিভ!\n🚀 সফল Creator-রা ফজরের পর কাজ শুরু করেন!",
        "⭐ ফজরের ওয়াক্ত! আল্লাহ ডাকছেন!\n🕌 নামাজ পড়ুন, দোয়া করুন!\n📈 আজকের ভিডিওর জন্য আল্লাহর কাছে বরকত চাইন!\n🔥 ফজর + কাজ = অপ্রতিরোধ্য সাফল্য!",
    ],
    "dhuhr": [
        "☀️ যোহরের সময়! একটু থামুন ভাইয়েরা!\n🕌 কাজ রেখে নামাজ পড়ুন — আল্লাহ বরকত দেবেন!\n💻 নামাজের পর Thumbnail নিয়ে কাজ করুন!\n🔥 বিরতি নিন, রিফ্রেশ হন, আরো ভালো করুন!",
        "🌞 দুপুর হলো — যোহরের নামাজ!\n🕌 ৫ মিনিট সব বন্ধ রেখে নামাজ পড়ুন!\n📊 নামাজের পর Analytics দেখুন!\n🎯 কোন ভিডিও ভালো চলছে বুঝুন!",
        "⏰ যোহরের আযান! কাজ পজ করুন!\n🕌 নামাজ পড়ুন, মন শান্ত করুন!\n🎬 নামাজের পর আজকের টার্গেট রিভিউ করুন!\n🚀 নামাজ পড়ে কাজ করলে বরকত হয়!",
    ],
    "asr": [
        "🌤️ আসরের সময় হয়েছে!\n🕌 নামাজ পড়ে নিন — দিন শেষ হওয়ার আগে!\n🎬 নামাজের পর ভিডিও এডিটিং শেষ করুন!\n💪 আর কয়েক ঘন্টা — আজকের টার্গেট পূরণ করুন!",
        "🌅 আসরের আযান দিয়েছে!\n🕌 নামাজ পড়ুন, আল্লাহর শুকরিয়া করুন!\n📈 নামাজের পর Comment reply দিন!\n🔥 Consistency-ই YouTube সাফল্যের চাবিকাঠি!",
        "⭐ আসরের নামাজের ওয়াক্ত!\n🕌 উঠুন, নামাজ পড়ুন!\n💻 নামাজের পর আগামীকালের ভিডিও প্ল্যান করুন!\n🌟 প্রতিদিন একটু এগোলেই বড় YouTuber হওয়া যায়!",
    ],
    "maghrib": [
        "🌇 মাগরিবের সময়! সন্ধ্যা হলো!\n🕌 দ্রুত নামাজ পড়ুন — সময় কম!\n📊 নামাজের পর আজকের Analytics দেখুন!\n🎯 আজকে কতটা এগোলেন হিসাব করুন!",
        "🌆 মাগরিবের আযান! সারাদিনের পর আল্লাহর কাছে!\n🕌 নামাজ পড়ুন, দোয়া করুন!\n🎬 নামাজের পর শেষ কাজটা গুছিয়ে নিন!\n💡 সন্ধ্যার পরিকল্পনা = কালকের সাফল্য!",
        "🌃 সন্ধ্যা হলো — মাগরিবের নামাজ!\n🕌 নামাজ পড়ুন!\n📈 নামাজের পর Subscriber count দেখুন!\n🔥 আজকে একটু বাড়লেও আলহামদুলিল্লাহ!",
    ],
    "isha": [
        "🌙 ইশার সময়! রাত শুরু হলো!\n🕌 দিনের শেষ নামাজ পড়ুন!\n💻 নামাজের পর আগামীকালের ভিডিও শিডিউল করুন!\n😴 কাজ শেষে তাড়াতাড়ি ঘুমান — ফজরে উঠতে হবে!",
        "⭐ ইশার আযান! দিনের শেষ ইবাদত!\n🕌 নামাজ পড়ুন, চ্যানেলের জন্য দোয়া করুন!\n📊 আজকের পুরো Analytics রিভিউ করুন!\n🌙 রাত ১২টার আগে ঘুমান — সফল Creator-দের রুটিন!",
        "🌟 ইশার নামাজের ওয়াক্ত!\n🕌 নামাজ পড়ে রাতের কাজ শুরু করুন!\n🎬 রাতে Script লিখুন — সকালে Shoot করুন!\n💪 আজকে ভালো কাজ করেছেন — আলহামদুলিল্লাহ!",
    ],
    "jummah": [
        "🕌✨ জুম্মার মোবারক! আজ পবিত্র শুক্রবার!\n📿 জুম্মার নামাজ মিস করবেন না!\n🤲 নামাজে চ্যানেলের জন্য বিশেষ দোয়া করুন!\n📈 জুম্মার দিনে Special Video দিন — ভিউ বেশি হয়!",
        "🌟 জুম্মা মোবারক ভাইয়েরা!\n🕌 আজকের সেরা ইবাদত — জুম্মার নামাজ!\n💫 নামাজের পর একটা ইসলামিক Content বানান!\n🚀 জুম্মার বরকতে Channel এগিয়ে যাক — আমিন!",
        "✨ আল্লাহু আকবার! জুম্মার দিন এলো!\n🕌 জুম্মার খুতবা শুনুন, নামাজ পড়ুন!\n📊 এই পবিত্র দিনে Channel-এর জন্য দোয়া করুন!\n💪 জুম্মার পর নতুন উদ্যমে কাজ শুরু করুন!",
    ],
}

# ─────────────────────────────────────────
# ঘন্টার মোটিভেশন
# ─────────────────────────────────────────
HOURLY_MESSAGES = [
    "⏰ ঘড়িতে {time} বাজলো!\n🎬 এই মুহূর্তে কী করছেন? ভিডিও বানাচ্ছেন তো?\n📈 প্রতি ঘন্টা মূল্যবান — একটু এগিয়ে যান!\n💪 আলহামদুলিল্লাহ, সুযোগ আছে — কাজে লাগান!",
    "🕐 {time} হলো! সময় চলে যাচ্ছে!\n🚀 YouTube-এ সফল হতে চাইলে এখনই কাজ করুন!\n🎯 আজকের টার্গেট পূরণ হয়েছে?\n✨ ছোট ছোট পদক্ষেপই বড় সাফল্য আনে!",
    "⌚ {time} বাজে! থামুন, ভাবুন!\n💡 আজকে নতুন কী শিখলেন YouTube সম্পর্কে?\n📊 Analytics দেখুন — কোন Video ভালো চলছে?\n🌟 আল্লাহ সুযোগ দিয়েছেন, কাজে লাগান!",
    "🔔 {time}! নতুন ঘন্টা শুরু!\n🎬 এই ঘন্টায় একটা কাজ শেষ করুন!\n📈 Consistency = YouTube সাফল্য!\n💪 বিসমিল্লাহ বলে শুরু করুন — বরকত হবে!",
    "⏳ {time} হয়ে গেল! সময় থামছে না!\n🚀 আজকে কতটা এগোলেন?\n🎯 একটা ভালো Thumbnail বানান এখনই!\n🤲 আল্লাহর উপর ভরসা + কাজ = সাফল্য!",
    "🌟 {time}! মোটিভেশন টাইম!\n💻 MrBeast প্রতিদিন কাজ করেন — আপনিও করুন!\n📊 আজকে একটা নতুন Video Idea লিখুন!\n✨ আলহামদুলিল্লাহ — আপনার Channel একদিন বড় হবেই!",
]

# ─────────────────────────────────────────
# /setup কমান্ড — গ্রুপে এড করে এটা লিখলেই চালু
# ─────────────────────────────────────────
async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat_title = update.message.chat.title or "এই চ্যাট"

    already_active = chat_id in active_chats
    active_chats.add(chat_id)
    save_chats(active_chats)

    prayers = get_prayer_times()
    now = datetime.now(DHAKA_TZ)
    weekday_names = ["সোমবার", "মঙ্গলবার", "বুধবার", "বৃহস্পতিবার", "শুক্রবার", "শনিবার", "রবিবার"]
    today = weekday_names[now.weekday()]

    if already_active:
        msg = (
            f"✅ «{chat_title}» আগে থেকেই Active আছে!\n\n"
            f"📅 আজকের নামাজের সময় ({today}):\n"
            f"🌅 ফজর:    {prayers['fajr'][0]:02d}:{prayers['fajr'][1]:02d}\n"
            f"☀️ যোহর:   {prayers['dhuhr'][0]:02d}:{prayers['dhuhr'][1]:02d}\n"
            f"🌤️ আসর:    {prayers['asr'][0]:02d}:{prayers['asr'][1]:02d}\n"
            f"🌇 মাগরিব: {prayers['maghrib'][0]:02d}:{prayers['maghrib'][1]:02d}\n"
            f"🌙 ইশা:    {prayers['isha'][0]:02d}:{prayers['isha'][1]:02d}\n\n"
            "🔔 নামাজ ও মোটিভেশন মেসেজ চলছে!\n"
            "বন্ধ করতে: /stop"
        )
    else:
        msg = (
            f"🎉 আসসালামু আলাইকুম!\n"
            f"✅ «{chat_title}» সফলভাবে Setup হয়েছে!\n\n"
            "এখন থেকে এই গ্রুপে পাবেন:\n"
            "🕌 প্রতিটি নামাজের সময় রিমাইন্ডার\n"
            "⏰ প্রতি ঘন্টায় YouTube মোটিভেশন (সকাল ৪টা - রাত ১১টা)\n"
            "🌟 শুক্রবারে জুম্মার বিশেষ বার্তা\n\n"
            f"📅 আজকের নামাজের সময় ({today}):\n"
            f"🌅 ফজর:    {prayers['fajr'][0]:02d}:{prayers['fajr'][1]:02d}\n"
            f"☀️ যোহর:   {prayers['dhuhr'][0]:02d}:{prayers['dhuhr'][1]:02d}\n"
            f"🌤️ আসর:    {prayers['asr'][0]:02d}:{prayers['asr'][1]:02d}\n"
            f"🌇 মাগরিব: {prayers['maghrib'][0]:02d}:{prayers['maghrib'][1]:02d}\n"
            f"🌙 ইশা:    {prayers['isha'][0]:02d}:{prayers['isha'][1]:02d}\n\n"
            "💪 আল্লাহর রহমতে আপনার Channel এগিয়ে যাক — আমিন!\n"
            "বন্ধ করতে: /stop"
        )
    await update.message.reply_text(msg)
    logger.info(f"Setup: {chat_title} ({chat_id})")

# ─────────────────────────────────────────
# /stop কমান্ড — গ্রুপ থেকে বট বন্ধ করতে
# ─────────────────────────────────────────
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat_title = update.message.chat.title or "এই চ্যাট"

    if chat_id in active_chats:
        active_chats.discard(chat_id)
        save_chats(active_chats)
        msg = (
            f"⛔ «{chat_title}» থেকে বট বন্ধ করা হয়েছে!\n\n"
            "আর কোনো অটো মেসেজ আসবে না।\n"
            "আবার চালু করতে: /setup"
        )
    else:
        msg = "ℹ️ এই গ্রুপে বট আগে থেকেই বন্ধ ছিল।\nচালু করতে: /setup"

    await update.message.reply_text(msg)
    logger.info(f"Stop: {chat_title} ({chat_id})")

# ─────────────────────────────────────────
# /start কমান্ড
# ─────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat = update.message.chat

    # গ্রুপে /start দিলে /setup এর দিকে পাঠাও
    if chat.type in ("group", "supergroup"):
        await update.message.reply_text(
            "🕌 আসসালামু আলাইকুম!\n"
            "গ্রুপে বট চালু করতে: /setup লিখুন!"
        )
        return

    # Private chat এ /start
    active_chats.add(chat_id)
    save_chats(active_chats)

    prayers = get_prayer_times()
    msg = (
        "🕌 আসসালামু আলাইকুম! Islamic YouTube Bot!\n\n"
        "📌 কমান্ড লিস্ট:\n"
        "/setup — গ্রুপে বট চালু করুন\n"
        "/prayer — আজকের নামাজের সময়\n"
        "/motivation — এখনই একটা মোটিভেশন\n"
        "/status — বট স্ট্যাটাস দেখুন\n"
        "/stop — বট বন্ধ করুন\n"
        "/help — সাহায্য\n\n"
        f"📅 আজকের নামাজের সময় (ঢাকা):\n"
        f"🌅 ফজর:    {prayers['fajr'][0]:02d}:{prayers['fajr'][1]:02d}\n"
        f"☀️ যোহর:   {prayers['dhuhr'][0]:02d}:{prayers['dhuhr'][1]:02d}\n"
        f"🌤️ আসর:    {prayers['asr'][0]:02d}:{prayers['asr'][1]:02d}\n"
        f"🌇 মাগরিব: {prayers['maghrib'][0]:02d}:{prayers['maghrib'][1]:02d}\n"
        f"🌙 ইশা:    {prayers['isha'][0]:02d}:{prayers['isha'][1]:02d}\n\n"
        "💪 আল্লাহর রহমতে আপনার Channel এগিয়ে যাক — আমিন!"
    )
    await update.message.reply_text(msg)

# ─────────────────────────────────────────
# /prayer কমান্ড
# ─────────────────────────────────────────
async def prayer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    active_chats.add(chat_id)
    save_chats(active_chats)

    prayers = get_prayer_times()
    now = datetime.now(DHAKA_TZ)
    time_str = now.strftime("%I:%M %p")
    weekday_names = ["সোমবার", "মঙ্গলবার", "বুধবার", "বৃহস্পতিবার", "শুক্রবার", "শনিবার", "রবিবার"]
    today = weekday_names[now.weekday()]

    # পরবর্তী নামাজ খুঁজে বের করা
    prayer_order = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    prayer_names_bn = {
        "fajr": "🌅 ফজর",
        "dhuhr": "☀️ যোহর",
        "asr": "🌤️ আসর",
        "maghrib": "🌇 মাগরিব",
        "isha": "🌙 ইশা",
    }
    next_prayer = None
    for p in prayer_order:
        h, m = prayers[p]
        if (now.hour, now.minute) < (h, m):
            next_prayer = p
            break

    msg = (
        f"🕌 আজকের নামাজের সময় — {today}\n"
        f"🕐 এখন: {time_str} (ঢাকা)\n\n"
        f"🌅 ফজর:   {prayers['fajr'][0]:02d}:{prayers['fajr'][1]:02d}\n"
        f"☀️ যোহর:  {prayers['dhuhr'][0]:02d}:{prayers['dhuhr'][1]:02d}\n"
        f"🌤️ আসর:   {prayers['asr'][0]:02d}:{prayers['asr'][1]:02d}\n"
        f"🌇 মাগরিব: {prayers['maghrib'][0]:02d}:{prayers['maghrib'][1]:02d}\n"
        f"🌙 ইশা:   {prayers['isha'][0]:02d}:{prayers['isha'][1]:02d}\n\n"
    )

    if next_prayer:
        h, m = prayers[next_prayer]
        msg += f"⏭️ পরবর্তী নামাজ: {prayer_names_bn[next_prayer]} — {h:02d}:{m:02d}\n\n"
    else:
        msg += "✅ আজকের সব নামাজ শেষ — আলহামদুলিল্লাহ!\n\n"

    if now.weekday() == 4:
        msg += "🕌 আজ শুক্রবার — জুম্মার নামাজ মিস করবেন না!\n"

    msg += "🤲 নামাজ পড়ুন, আল্লাহর রহমত নিন!"
    await update.message.reply_text(msg)

# ─────────────────────────────────────────
# /motivation কমান্ড
# ─────────────────────────────────────────
async def motivation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    active_chats.add(chat_id)
    save_chats(active_chats)

    now = datetime.now(DHAKA_TZ)
    time_str = now.strftime("%I:%M %p")
    msg = random.choice(HOURLY_MESSAGES).format(time=time_str)
    await update.message.reply_text(msg)

# ─────────────────────────────────────────
# /status কমান্ড
# ─────────────────────────────────────────
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    active_chats.add(chat_id)
    save_chats(active_chats)

    now = datetime.now(DHAKA_TZ)
    time_str = now.strftime("%d %B %Y, %I:%M %p")
    msg = (
        "✅ বট সম্পূর্ণ Active আছে!\n\n"
        f"🕐 ঢাকার সময়: {time_str}\n"
        f"👥 Setup করা গ্রুপ/চ্যাট: {len(active_chats)}টি\n\n"
        "⚙️ চলছে:\n"
        "• প্রতি মিনিটে নামাজের সময় চেক\n"
        "• প্রতি ঘন্টায় মোটিভেশন (সকাল ৪টা - রাত ১১টা)\n"
        "• জুম্মার বিশেষ মেসেজ (শুক্রবার)\n\n"
        "💡 নতুন গ্রুপে যোগ করলে /setup লিখুন!\n"
        "🤲 আলহামদুলিল্লাহ — সব ঠিকঠাক!"
    )
    await update.message.reply_text(msg)

# ─────────────────────────────────────────
# /help কমান্ড
# ─────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    active_chats.add(chat_id)
    save_chats(active_chats)

    msg = (
        "🕌 Islamic YouTube Bot — Help\n\n"
        "📌 কমান্ড:\n"
        "/setup — গ্রুপে বট চালু করুন ✅\n"
        "/stop — বট বন্ধ করুন ⛔\n"
        "/prayer — আজকের নামাজের সময় 🕌\n"
        "/motivation — এখনই মোটিভেশন পান 🚀\n"
        "/status — বট স্ট্যাটাস দেখুন 📊\n"
        "/help — এই সাহায্য বার্তা ℹ️\n\n"
        "🔔 অটো মেসেজ (/setup এর পর):\n"
        "• প্রতিটি নামাজের সময় রিমাইন্ডার\n"
        "• প্রতি ঘন্টায় YouTube মোটিভেশন\n"
        "• শুক্রবারে জুম্মার বিশেষ বার্তা\n\n"
        "💬 'নামাজ', 'সময়', 'prayer' লিখলেও নামাজের সময় পাবেন!\n\n"
        "💪 আল্লাহর রহমতে এগিয়ে যান!"
    )
    await update.message.reply_text(msg)

# ─────────────────────────────────────────
# সাধারণ মেসেজে নামাজের সময় (keyword detect)
# ─────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat.id
    active_chats.add(chat_id)
    save_chats(active_chats)

    text = update.message.text.lower()

    # নামাজের সময় জিজ্ঞেস করলে
    prayer_keywords = [
        "নামাজ", "সালাত", "prayer", "ফজর", "যোহর", "আসর", "মাগরিব", "ইশা",
        "সময়", "time", "আজান", "আযান", "জুম্মা", "namaz", "salah"
    ]

    if any(kw in text for kw in prayer_keywords):
        # prayer_command এর মতো reply দিন
        prayers = get_prayer_times()
        now = datetime.now(DHAKA_TZ)
        time_str = now.strftime("%I:%M %p")
        weekday_names = ["সোমবার", "মঙ্গলবার", "বুধবার", "বৃহস্পতিবার", "শুক্রবার", "শনিবার", "রবিবার"]
        today = weekday_names[now.weekday()]

        prayer_order = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        next_prayer = None
        prayer_names_bn = {
            "fajr": "🌅 ফজর",
            "dhuhr": "☀️ যোহর",
            "asr": "🌤️ আসর",
            "maghrib": "🌇 মাগরিব",
            "isha": "🌙 ইশা",
        }
        for p in prayer_order:
            h, m = prayers[p]
            if (now.hour, now.minute) < (h, m):
                next_prayer = p
                break

        msg = (
            f"🕌 আজকের নামাজের সময় — {today}\n"
            f"🕐 এখন: {time_str} (ঢাকা)\n\n"
            f"🌅 ফজর:    {prayers['fajr'][0]:02d}:{prayers['fajr'][1]:02d}\n"
            f"☀️ যোহর:   {prayers['dhuhr'][0]:02d}:{prayers['dhuhr'][1]:02d}\n"
            f"🌤️ আসর:    {prayers['asr'][0]:02d}:{prayers['asr'][1]:02d}\n"
            f"🌇 মাগরিব: {prayers['maghrib'][0]:02d}:{prayers['maghrib'][1]:02d}\n"
            f"🌙 ইশা:    {prayers['isha'][0]:02d}:{prayers['isha'][1]:02d}\n\n"
        )
        if next_prayer:
            h, m = prayers[next_prayer]
            msg += f"⏭️ পরবর্তী নামাজ: {prayer_names_bn[next_prayer]} — {h:02d}:{m:02d}\n\n"
        else:
            msg += "✅ আজকের সব নামাজ শেষ — আলহামদুলিল্লাহ!\n\n"

        if now.weekday() == 4:
            msg += "🕌 আজ শুক্রবার — জুম্মার নামাজ মিস করবেন না!\n"

        msg += "🤲 নামাজ পড়ুন, বরকত নিন!"
        await update.message.reply_text(msg)

# ─────────────────────────────────────────
# অটো: নামাজের সময় চেক (প্রতি মিনিট)
# ─────────────────────────────────────────
async def check_prayer_times(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(DHAKA_TZ)
    hour, minute = now.hour, now.minute
    weekday = now.weekday()
    time_str = now.strftime("%I:%M %p")
    prayers = get_prayer_times()

    triggered = None
    for name, (h, m) in prayers.items():
        if hour == h and minute == m:
            triggered = name
            break

    if not triggered:
        return

    if triggered == "dhuhr" and weekday == 4:
        msg = random.choice(PRAYER_MESSAGES["jummah"])
    else:
        msg = random.choice(PRAYER_MESSAGES[triggered])

    msg += f"\n\n🕐 সময়: {time_str} (ঢাকা)"

    for chat_id in list(active_chats):
        try:
            await context.bot.send_message(chat_id=chat_id, text=msg)
        except Exception as e:
            logger.warning(f"Error sending to {chat_id}: {e}")
            active_chats.discard(chat_id)
            save_chats(active_chats)

# ─────────────────────────────────────────
# অটো: ঘন্টার মোটিভেশন
# ─────────────────────────────────────────
async def send_hourly_motivation(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(DHAKA_TZ)
    if now.minute != 0:
        return
    if now.hour >= 23 or now.hour < 4:
        return

    prayers = get_prayer_times()
    prayer_hours = [v[0] for v in prayers.values()]
    if now.hour in prayer_hours:
        return

    time_str = now.strftime("%I:%M %p")
    msg = random.choice(HOURLY_MESSAGES).format(time=time_str)

    for chat_id in list(active_chats):
        try:
            await context.bot.send_message(chat_id=chat_id, text=msg)
        except Exception as e:
            logger.warning(f"Error sending to {chat_id}: {e}")
            active_chats.discard(chat_id)
            save_chats(active_chats)

# ─────────────────────────────────────────
# মেইন
# ─────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN environment variable নেই!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("setup", setup_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("prayer", prayer_command))
    app.add_handler(CommandHandler("motivation", motivation_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("help", help_command))

    # Message Handler (keyword detect)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Job Queue (অটো মেসেজ)
    app.job_queue.run_repeating(check_prayer_times, interval=60, first=10)
    app.job_queue.run_repeating(send_hourly_motivation, interval=60, first=30)

    print("🕌 Islamic YouTube Bot চালু! সব কমান্ড Active!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
