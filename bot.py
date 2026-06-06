```python
from telethon import TelegramClient, events
from flask import Flask
import threading
import hashlib
import re
import os

# ===== تنظیمات (API خودت) =====
API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"

# کانال‌های منبع (سه تا)
SOURCE_CHANNELS = [
    "KhabarFori",
    "KhabarFooury",
    "akharinkhabar",
    "Projectmeshkat"      # کانال مشکات
]

DEST_CHANNEL = "@yarakhabar"
MY_SIGNATURE = "\n\n@YARAKHABAR📢\n🔷🔹🎯هر لحظه یک خبر تازه🎯🔹🔷"

# کلمات ممنوعه (تبلیغ، شرط‌بندی و ...)
BLOCKED_WORDS = [
    "تبلیغ", "خرید", "فروش", "کسب درآمد", "عضویت", "ارزان", "تخفیف",
    "ویژه", "همین الان", "کلیک کن", "دانلود", "فیلترشکن", "vpn",
    "سرعت عالی", "امنیت بالا", "اتصال پایدار", "فروشی", "مفت", "حراج",
    "ارزون", "ثبت نام", "رایگان", "شرط‌بندی", "شرط بندی", "bet",
    "کازینو", "قمار", "پیش‌بینی ورزشی", "برد تضمینی", "استروئید",
    "فیلم سوپر", "عکس خصوصی", "همسریابی", "دوستیابی"
]

# امضاهایی که باید از متن خبر حذف شوند
TEXTS_TO_REMOVE = [
    "@akharinkhabar", "@Akharinkhabar", "@AKHARINKHABAR",
    "@KhabarFori", "@khabarfori", "@KHABARFORI", "@KhabarFooury",
    "@Projectmeshkat", "@projectmeshkat", "Projectmeshkat",
    "آخرین خبر در روبیکا", "آخرین خبر در ایتا", "آخرین خبر در بله",
    "t.me/Projectmeshkat", "https://zil.ink/ProjectMeshkat"
]

# ===== حافظه برای جلوگیری از تکراری‌ها =====
recent_hashes = []
MAX_HISTORY = 1000

def normalize(text):
    if not text:
        return ""
    text = text.replace("\u200c", " ")         # نیم‌فاصله
    text = text.replace("ي", "ی").replace("ك", "ک")  # حروف عربی
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def clean_text(text):
    if not text:
        return ""
    for item in TEXTS_TO_REMOVE:
        text = text.replace(item, "")
    text = re.sub(r"https?://\S+", "", text)   # حذف لینک‌ها
    text = re.sub(r"@[^\s]+", "", text)        # حذف باقی‌مانده منشن‌ها
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
    text = re.sub(r"\d+", "", text)            # حذف اعداد
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text) # فقط حروف فارسی/انگلیسی
    return " ".join(text.split()[:30])

def get_hash(text):
    return hashlib.md5(simplify(text).encode("utf-8")).hexdigest()

def is_duplicate(text):
    return get_hash(text) in recent_hashes

def add_to_history(text):
    recent_hashes.append(get_hash(text))
    if len(recent_hashes) > MAX_HISTORY:
        recent_hashes.pop(0)

# ===== اتصال تلگرام =====
client = TelegramClient("yarakhabar_session", API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    try:
        msg = event.message
        text = msg.message or ""
        if not text.strip():
            return

        # ۱. چک کردن کلمات تبلیغاتی (روی متن اصلی)
        if contains_blocked(text):
            print("⛔ تبلیغ")
            return

        # ۲. حذف امضاها و لینک‌ها
        cleaned = clean_text(text)

        # ۳. بررسی طول
        if is_rubbish(cleaned) or len(cleaned) < 10:
            print("⛔ کوتاه یا بی‌ارزش")
            return

        # ۴. تشخیص تکراری
        if is_duplicate(cleaned):
            print("⛔ تکراری")
            return

        add_to_history(cleaned)

        header = "🚨🌟❇️🚨"
        final_text = f"{header}\n{cleaned}\n{header}{MY_SIGNATURE}"

        # ۵. ارسال
        if msg.media:
            await client.send_message(DEST_CHANNEL, final_text, file=msg.media)
        else:
            await client.send_message(DEST_CHANNEL, final_text)

        print("✅ ارسال شد")

    except Exception as e:
        print("❌ خطا:", e)

# ===== وب سرور (برای رایگان نخوابیدن در Railway) =====
app = Flask(__name__)

@app.route("/")
def home():
    return "YaraKhabar Bot is Running!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# ===== اجرای همزمان ربات و وب‌سرور =====
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    print("🚀 ربات خبری احسان شروع به کار کرد...")
    with client:
        client.run_until_disconnected()
