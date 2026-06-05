from telethon import TelegramClient, events
from flask import Flask
from collections import deque
import threading
import hashlib
import re
import os
from dotenv import load_dotenv

# =========================
# تنظیمات
# =========================
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SOURCE_CHANNELS = [
    "KhabarFori",
    "KhabarFooury",
    "akharinkhabar"
]

DEST_CHANNEL = "@YARAKHABAR"
MY_SIGNATURE = "\n\n@YARAKHABAR📢\n🔷🔹🎯هر لحظه یک خبر تازه🎯🔹🔷"

BLOCKED_WORDS = [
    "تبلیغ", "خرید", "فروش", "کسب درآمد", "عضویت", "ارزان", "تخفیف",
    "ویژه", "همین الان", "کلیک کن", "دانلود", "فیلترشکن", "vpn",
    "سرعت عالی", "امنیت بالا", "اتصال پایدار", "فروشی", "مفت", "حراج",
    "ارزون", "ثبت نام", "رایگان", "شرط‌بندی", "شرط بندی", "bet",
    "کازینو", "قمار", "پیش‌بینی ورزشی", "برد تضمینی", "استروئید",
    "فیلم سوپر", "عکس خصوصی", "همسریابی", "دوستیابی"
]

TEXTS_TO_REMOVE = [
    "@akharinkhabar", "@Akharinkhabar", "@AKHARINKHABAR",
    "@KhabarFori", "@khabarfori", "@KHABARFORI", "@KhabarFooury",
    "آخرین خبر در روبیکا", "آخرین خبر در ایتا", "آخرین خبر در بله"
]

# =========================
# حافظه خبرهای اخیر
# =========================
recent_hashes = deque(maxlen=1000)

# =========================
# توابع کمکی
# =========================
def normalize(text):
    if not text:
        return ""
    text = text.replace("\u200c", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def clean(text):
    if not text:
        return ""
    for item in TEXTS_TO_REMOVE:
        text = text.replace(item, "")
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"@[^\s]+", "", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()

def is_rubbish(text):
    if not text:
        return True
    if len(text.strip()) < 10:
        return True
    return False

def contains_blocked(text):
    text = normalize(text).lower()
    for bad in BLOCKED_WORDS:
        if bad.lower() in text:
            return True
    return False

def simplify(text):
    text = normalize(text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    return " ".join(text.split()[:30])

def get_hash(text):
    return hashlib.md5(simplify(text).encode("utf-8")).hexdigest()

def is_duplicate(text):
    return get_hash(text) in recent_hashes

def add_history(text):
    recent_hashes.append(get_hash(text))

# =========================
# تلگرام
# =========================
client = TelegramClient(
    "yarakhabar_session",
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    try:
        msg = event.message

        text = msg.message or ""
        if not text.strip():
            return

        cleaned = clean(text)

        if is_rubbish(cleaned):
            print("⛔ بی‌ارزش")
            return

        if contains_blocked(cleaned):
            print("⛔ تبلیغ")
            return

        if len(cleaned) < 10:
            print("⛔ کوتاه")
            return

        if is_duplicate(cleaned):
            print("⛔ تکراری")
            return

        add_history(cleaned)

        header = "🚨🌟♦️🚨"
        final_text = (
            f"{header}\n"
            f"{cleaned}\n"
            f"{header}"
            f"{MY_SIGNATURE}"
        )

        if msg.media:
            await client.send_message(
                DEST_CHANNEL,
                final_text,
                file=msg.media
            )
        else:
            await client.send_message(
                DEST_CHANNEL,
                final_text
            )
        print("✅ ارسال شد")

    except Exception as e:
        print("❌ خطا:", e)

# =========================
# وب سرور
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "YaraKhabar Bot Running"

def run_web():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        threaded=True
    )

# =========================
# اجرا
# =========================
if __name__ == "__main__":
