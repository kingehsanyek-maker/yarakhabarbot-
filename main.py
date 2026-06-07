import os
import time
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from flask import Flask
import threading
import hashlib
import re

# ===== تنظیمات =====
API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"
SESSION_STRING = os.environ.get("SESSION_STRING", "")

SOURCE_CHANNELS = [
    "KhabarFori", "KhabarFooury", "akharinkhabar", "Projectmeshkat"
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

TEXTS_TO_REMOVE = [
    "@akharinkhabar", "@Akharinkhabar", "@AKHARINKHABAR",
    "akharinkhabar", "Akharinkhabar", "AKHARINKHABAR",
    "@akharinkhabar | akharinkhabar.ir",
    "| akharinkhabar.ir", " | akharinkhabar.ir",
    "akharinkhabar.ir", "www.akharinkhabar.ir",
    "http://akharinkhabar.ir", "https://akharinkhabar.ir",
    "t.me/akharinkhabar", "https://t.me/akharinkhabar",
    "#akharinkhabar", "#Akharinkhabar",
    "@KhabarFori", "@khabarfori", "@KHABARFORI",
    "KhabarFori", "khabarfori", "KHABARFORI",
    "t.me/KhabarFori", "https://t.me/KhabarFori",
    "@KhabarFooury", "@khabarfooury", "@KHABARFOOURY",
    "t.me/KhabarFooury", "https://t.me/KhabarFooury",
    "@Projectmeshkat", "@projectmeshkat", "@PROJECTMESHKAT",
    "Projectmeshkat", "projectmeshkat",
    "t.me/Projectmeshkat", "https://t.me/Projectmeshkat",
    "zil.ink/ProjectMeshkat", "https://zil.ink/ProjectMeshkat",
    "آخرین خبر در روبیکا", "آخرین خبر در ایتا", "آخرین خبر در بله",
]

recent_hashes = []
MAX_HISTORY = 1000

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
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\S*\.ir\S*", "", text)
    for item in TEXTS_TO_REMOVE:
        text = text.replace(item, "")
    text = re.sub(r"@[^\s]+", "", text)
    text = re.sub(r"\|\s*", "", text)
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

def add_to_history(text):
    recent_hashes.append(get_hash(text))
    if len(recent_hashes) > MAX_HISTORY:
        recent_hashes.pop(0)

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# متغیر ذخیرهٔ entity کانال مقصد (برای استفادهٔ دوباره)
dest_entity = None

async def resolve_dest():
    global dest_entity
    try:
        dest_entity = await client.get_entity(DEST_CHANNEL)
        print(f"✅ کانال مقصد {DEST_CHANNEL} پیدا شد.")
    except Exception as e:
        print(f"❌ خطا در پیدا کردن کانال مقصد: {e}")

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

        # تلاش برای ارسال با مدیریت FloodWait
        global dest_entity
        for attempt in range(3):
            try:
                if dest_entity is None:
                    await resolve_dest()
                if msg.media:
                    await client.send_message(dest_entity or DEST_CHANNEL, final_text, file=msg.media)
                else:
                    await client.send_message(dest_entity or DEST_CHANNEL, final_text)
                print("✅ ارسال شد")
                break
            except FloodWaitError as e:
                print(f"⏳ FloodWait: صبر {e.seconds} ثانیه...")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"❌ خطا در ارسال (تلاش {attempt+1}): {e}")
                await asyncio.sleep(5)
        else:
            print("❌ ارسال پیام پس از ۳ تلاش ناموفق ماند.")

        # مکث کوچک برای جلوگیری از Rate Limit
        await asyncio.sleep(2)

    except Exception as e:
        print("❌ خطا:", e)

# ===== پاک‌سازی حافظه دوره‌ای =====
def memory_cleaner():
    while True:
        time.sleep(6 * 3600)
        if len(recent_hashes) > 200:
            del recent_hashes[:-200]
            print("🧹 حافظه پاکسازی شد.")

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
        print("❌ SESSION_STRING تنظیم نشده.")
    else:
        threading.Thread(target=memory_cleaner, daemon=True).start()
        threading.Thread(target=run_web, daemon=True).start()
        print("🚀 ربات با مدیریت Rate Limit شروع کرد...")
        with client:
            client.loop.run_until_complete(resolve_dest())
            client.run_until_disconnected()
