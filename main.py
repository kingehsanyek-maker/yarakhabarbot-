from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from collections import deque
import threading
import hashlib
import re
import os
import logging
import sys

# --------------------- تنظیمات ---------------------
# ❗️ این مقادیر را با api_id و api_hash واقعی خود جایگزین کنید
API_ID = 31166081          # ← عدد واقعی از my.telegram.org
API_HASH = "5a19b28b0417beeb45b23cbf77586257"  # ← رشته واقعی

SOURCE_CHANNELS = ["KhabarFori", "KhabarFooury", "akharinkhabar"]
DEST_CHANNEL = -1002471046678
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

recent_hashes = deque(maxlen=1000)

# --------------------- توابع کمکی ---------------------
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
    return not text or len(text.strip()) < 10

def contains_blocked(text):
    text = normalize(text).lower()
    return any(bad.lower() in text for bad in BLOCKED_WORDS)

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

# --------------------- راه‌اندازی تلگرام ---------------------
# انتخاب روش سشن: StringSession (از متغیر محیطی) یا فایل
SESSION_STRING = os.environ.get("SESSION_STRING")
if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    print("📱 استفاده از StringSession برای ورود...")
else:
    # استفاده از فایل سشن (باید قبلاً در سیستم شخصی ساخته شده باشد)
    session_file = "yarakhabar_user"
    if not os.path.exists(f"{session_file}.session"):
        print("❌ فایل سشن پیدا نشد و SESSION_STRING تنظیم نشده است.")
        print("   لطفاً ابتدا روی سیستم خود فایل سشن را ایجاد کنید یا SESSION_STRING را تنظیم کنید.")
        print("   فلاسک همچنان اجرا می‌شود، اما ربات تلگرام فعال نیست.")
        client = None  # برای جلوگیری از اجرای ناقص
    else:
        client = TelegramClient(session_file, API_ID, API_HASH)
        print("📁 استفاده از فایل سشن برای ورود...")

# --------------------- هندلر پیام ---------------------
if client:
    @client.on(events.NewMessage(chats=SOURCE_CHANNELS))
    async def handler(event):
        try:
            msg = event.message
            text = msg.message or ""
            cleaned = clean(text)

            if is_rubbish(cleaned) or contains_blocked(cleaned) or is_duplicate(cleaned):
                return

            add_history(cleaned)
            header = "🚨🌟♦️🚨"
            final_text = f"{header}\n{cleaned}\n{header}{MY_SIGNATURE}"

            if msg.media:
                await client.send_message(DEST_CHANNEL, final_text, file=msg.media)
            else:
                await client.send_message(DEST_CHANNEL, final_text)

            print("✅ ارسال شد")

        except Exception as e:
            print("❌ خطا:", e)

# --------------------- فلاسک (Keep-Alive) ---------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "YaraKhabar User Client Running"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    # اجرای فلاسک در نخ جداگانه
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port),
        daemon=True
    ).start()

# --------------------- اجرای اصلی ---------------------
if __name__ == "__main__":
    print("🚀 Starting YaraKhabarBot...")
    logging.basicConfig(level=logging.INFO)

    # ابتدا وب سرور را راه می‌اندازیم
    run_web()

    if client is None:
        print("⚠️ کلاینت تلگرام راه‌اندازی نشد. فقط وب سرور فعال است.")
        # یک حلقه بی‌نهایت برای زنده نگه داشتن برنامه
        import time
        while True:
            time.sleep(3600)
    else:
        # اگر کلاینت وجود دارد، آن را اجرا کن
        try:
            print("📡 در حال اتصال به تلگرام...")
            client.start()  # اگر فایل سشن معتبر باشد، بدون پرسش وارد می‌شود
            print("✅ ربات تلگرام فعال شد!")
            client.run_until_disconnected()
        except Exception as e:
            print(f"❌ خطا در اتصال به تلگرام: {e}")
            # حتی اگر خطا بخورد، فلاسک همچنان از نخ دیگر فعال است
            import time
            while True:
                time.sleep(3600)
