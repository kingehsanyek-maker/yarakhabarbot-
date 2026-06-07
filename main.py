import os
import time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
import threading
import hashlib
import re

# ===== تنظیمات =====
API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"

SESSION_STRING = os.environ.get("SESSION_STRING", "")

SOURCE_CHANNELS = [
    "KhabarFori",
    "KhabarFooury",
    "akharinkhabar",
    "Projectmeshkat"
]

DEST_CHANNEL = "@yarakhabar"
MY_SIGNATURE = "\n\n@YARAKHABAR📢\n🔷🔹🎯هر لحظه یک خبر تازه🎯🔹🔷"

BLOCKED_WORDS = [
    "تبلیغ", "خرید", "فروش", "کسب درآمد", "عضویت", "ارزان", "تخفیف",
    "ویژه", "همین الان", "کلیک کن", "دانلود", "فیلترشکن", "vpn",
    "سرعت عالی", "امنیت بالا", "اتصال پایدار", "فروشی", "مفت", "حراج",
    "ارزون", "ثبت نام", "رایگان", "شرط‌بندی", "شرط بندی", "bet",
    "کازینو", "قمار", "پیش‌بینی ورزشی", "برد تضمینی", "استروئید",
    "فیلم سوپر", "عکس خصوصی", "همسریابی", "دوستیابی"
]

# ===== لیست جامع امضاها و لینک‌های منبع =====
TEXTS_TO_REMOVE = [
    # --- akharinkhabar ---
    "@akharinkhabar", "@Akharinkhabar", "@AKHARINKHABAR",
    "akharinkhabar", "Akharinkhabar", "AKHARINKHABAR",
    "@akharinkhabar | akharinkhabar.ir",
    "@Akharinkhabar | akharinkhabar.ir",
    "| akharinkhabar.ir", " | akharinkhabar.ir",
    "akharinkhabar.ir", "www.akharinkhabar.ir",
    "http://akharinkhabar.ir", "https://akharinkhabar.ir",
    "http://www.akharinkhabar.ir", "https://www.akharinkhabar.ir",
    "t.me/akharinkhabar", "https://t.me/akharinkhabar",
    "t.me/Akharinkhabar", "https://t.me/Akharinkhabar",
    "#akharinkhabar", "#Akharinkhabar",
    # --- KhabarFori ---
    "@KhabarFori", "@khabarfori", "@KHABARFORI",
    "KhabarFori", "khabarfori", "KHABARFORI",
    "@KhabarFori |", "| KhabarFori",
    "t.me/KhabarFori", "https://t.me/KhabarFori",
    "t.me/khabarfori", "https://t.me/khabarfori",
    "#KhabarFori", "#khabarfori",
    # --- KhabarFooury ---
    "@KhabarFooury", "@khabarfooury", "@KHABARFOOURY",
    "KhabarFooury", "khabarfooury",
    "t.me/KhabarFooury", "https://t.me/KhabarFooury",
    "#KhabarFooury",
    # --- Projectmeshkat ---
    "@Projectmeshkat", "@projectmeshkat", "@PROJECTMESHKAT",
    "Projectmeshkat", "projectmeshkat",
    "t.me/Projectmeshkat", "https://t.me/Projectmeshkat",
    "zil.ink/ProjectMeshkat", "https://zil.ink/ProjectMeshkat",
    "#Projectmeshkat", "#projectmeshkat",
    # --- عبارات فارسی ---
    "آخرین خبر در روبیکا", "آخرین خبر در ایتا", "آخرین خبر در بله",
    "پایگاه خبری", "خبرگزاری",
]

# ===== حافظه برای تشخیص تکراری =====
recent_hashes = []
MAX_HISTORY = 1000

# ===== توابع کمکی =====
def normalize(text):
    if not text:
        return ""
    text = text.replace("\u200c", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def clean_text(text):
    if not text:
        return ""
    # ۱. حذف لینک‌های کامل (http/https)
    text = re.sub(r"https?://\S+", "", text)
    # ۲. حذف دامنه‌های .ir که بدون پروتکل مانده‌اند (مثل .ir, | .ir, akharinkhabar.ir)
    text = re.sub(r"\S*\.ir\S*", "", text)
    # ۳. حذف امضاهای مشخص
    for item in TEXTS_TO_REMOVE:
        text = text.replace(item, "")
    # ۴. حذف باقی‌ماندهٔ منشن‌ها (@xxx)
    text = re.sub(r"@[^\s]+", "", text)
    # ۵. حذف باقی‌ماندهٔ لوله‌ها و فاصله‌های اضافی (مثل " | ")
    text = re.sub(r"\|\s*", "", text)
    # ۶. حذف خط‌های خالی اضافی
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()

def is_rubbish(text):
    if not text or len(text.strip()) < 10:
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

def add_to_history(text):
    recent_hashes.append(get_hash(text))
    if len(recent_hashes) > MAX_HISTORY:
        recent_hashes.pop(0)

def memory_cleaner():
    """هر ۶ ساعت حافظه را خلوت می‌کند (فقط ۲۰۰ خبر آخر را نگه می‌دارد)"""
    while True:
        time.sleep(6 * 3600)  # ۶ ساعت
        global recent_hashes
        if len(recent_hashes) > 200:
            recent_hashes = recent_hashes[-200:]
            print("🧹 حافظه پاکسازی شد (۲۰۰ خبر آخر حفظ شد)")

# ===== ربات تلگرامی =====
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    try:
        msg = event.message
        text = msg.message or ""
        if not text.strip():
            return

        if contains_blocked(text):
            print("⛔ تبلیغ")
            return

        cleaned = clean_text(text)
        if is_rubbish(cleaned):
            print("⛔ بی‌ارزش")
            return

        if is_duplicate(cleaned):
            print("⛔ تکراری")
            return

        add_to_history(cleaned)

        header = "🚨🌟♦️🚨"
        final_text = f"{header}\n{cleaned}\n{header}{MY_SIGNATURE}"

        if msg.media:
            await client.send_message(DEST_CHANNEL, final_text, file=msg.media)
        else:
            await client.send_message(DEST_CHANNEL, final_text)

        print("✅ ارسال شد")

    except Exception as e:
        print("❌ خطا:", e)

# ===== وب‌سرور =====
app = Flask(__name__)

@app.route("/")
def home():
    return "YaraKhabar Bot is Running!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# ===== اجرای اصلی =====
if __name__ == "__main__":
    if not SESSION_STRING:
        print("❌ SESSION_STRING تنظیم نشده است. ربات راه‌اندازی نشد.")
    else:
        # راه‌اندازی نخ پاک‌سازی حافظه
        threading.Thread(target=memory_cleaner, daemon=True).start()
        # راه‌اندازی وب‌سرور
        threading.Thread(target=run_web, daemon=True).start()
        print("🚀 ربات نهایی احسان (با شکارچی .ir و پاک‌کننده خودکار) روشن شد...")
        with client:
            client.run_until_disconnected()
