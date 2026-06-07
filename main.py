import os, time, asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from flask import Flask
import threading, hashlib, re

API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"
SESSION_STRING = os.environ.get("SESSION_STRING", "")

SOURCE_CHANNELS = ["KhabarFori", "KhabarFooury", "akharinkhabar", "Projectmeshkat"]
DEST_CHANNEL = "@yarakhabar"
MY_SIGNATURE = "\n@YARAKHABAR📢\n🔷🔹🎯هر لحظه یک خبر تازه🎯🔹🔷"

# ===== دیکشنری کلمات کلیدی به ایموجی (اولویت با ترتیب همین لیست) =====
KEYWORD_EMOJI = {
    # --- مقامات و مفاهیم آمریکا (توهین‌آمیز) ---
    "ترامپ": "🐒", "بایدن": "🐒", "پنس": "🐒", "آمریکا": "🐒",
    "ایالات متحده": "🐒", "واشنگتن": "🐒", "کاخ سفید": "🐒",
    # --- اسرائیل (توهین‌آمیز) ---
    "اسرائیل": "🐀", "نتانیاهو": "🐀", "صهیونیست": "🐀", "تل‌آویو": "🐀",
    # --- زلنسکی (توهین‌آمیز) ---
    "زلنسکی": "🐴",
    # --- روسیه (با احترام) ---
    "روسیه": "🇷🇺", "پوتین": "🇷🇺", "مسکو": "🇷🇺",
    # --- اوکراین (با احترام) ---
    "اوکراین": "🇺🇦", "کیف": "🇺🇦",
    # --- چین ---
    "چین": "🇨🇳", "شی جین پینگ": "🇨🇳", "پکن": "🇨🇳",
    # --- ایران (خنثی) ---
    "ایران": "🇮🇷", "تهران": "🇮🇷",
    # --- فرانسه ---
    "فرانسه": "🇫🇷", "مکرون": "🇫🇷",
    # --- انگلستان ---
    "انگلیس": "🇬🇧", "لندن": "🇬🇧", "بوریس جانسون": "🇬🇧",
    # --- آلمان ---
    "آلمان": "🇩🇪", "برلین": "🇩🇪",
    # --- نظامی و بحران ---
    "جنگ": "⚔️", "حمله": "💣", "موشک": "🚀", "هسته‌ای": "☢️",
    "زلزله": "🌍", "سیل": "🌊", "آتش‌سوزی": "🔥",
    # --- ورزش ---
    "فوتبال": "⚽", "والیبال": "🏐", "کشتی": "🤼", "بسکتبال": "🏀",
    # --- سایر ---
    "سفر": "✈️", "دیدار": "🤝", "توافق": "📝", "اقتصاد": "💰", "نفت": "🛢️",
}

# ایموجی‌های پیش‌فرض برای خبرهای معمولی
DEFAULT_EMOJIS = ("🌟", "❇️")

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
    "| akharinkhabar.ir", "akharinkhabar.ir",
    "t.me/akharinkhabar", "https://t.me/akharinkhabar",
    "@KhabarFori", "@khabarfori", "@KHABARFORI",
    "t.me/KhabarFori", "https://t.me/KhabarFori",
    "@KhabarFooury", "t.me/KhabarFooury",
    "@Projectmeshkat", "t.me/Projectmeshkat",
    "https://zil.ink/ProjectMeshkat",
    "آخرین خبر در روبیکا", "آخرین خبر در ایتا", "آخرین خبر در بله",
]

recent_hashes = []
MAX_HISTORY = 1000

def normalize(text):
    if not text: return ""
    text = text.replace("\u200c", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")
    return re.sub(r"\s+", " ", text).strip()

def clean_text(text):
    if not text: return ""
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
    return any(bad in normalize(text).lower() for bad in BLOCKED_WORDS)

def simplify(text):
    text = normalize(text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    return " ".join(text.split()[:30])

def get_hash(text):
    return hashlib.md5(simplify(text).encode()).hexdigest()

def is_duplicate(text):
    return get_hash(text) in recent_hashes

def add_to_history(text):
    recent_hashes.append(get_hash(text))
    if len(recent_hashes) > MAX_HISTORY: recent_hashes.pop(0)

def generate_header(text):
    """تولید header هوشمند با دو ایموجی بین 🚨ها"""
    norm = normalize(text).lower()
    found = []
    # اسکن کلمات کلیدی به ترتیب دیکشنری
    for keyword, emoji in KEYWORD_EMOJI.items():
        if keyword in norm:
            found.append(emoji)
    # حذف تکراری‌ها با حفظ ترتیب
    uniq = []
    for em in found:
        if em not in uniq:
            uniq.append(em)
    found = uniq

    if not found:
        # خبر معمولی: دو ایموجی پیش‌فرض
        return f"🚨{DEFAULT_EMOJIS[0]}{DEFAULT_EMOJIS[1]}🚨"

    if len(found) == 1:
        single = found[0]
        # اگر فقط یک ایموجی پیدا شد، ممکن است نیاز به جفت توهین‌آمیز داشته باشد
        text_has_israel = any(w in norm for w in ["اسرائیل", "نتانیاهو", "صهیونیست", "تل‌آویو"])
        text_has_us = any(w in norm for w in ["آمریکا", "ترامپ", "بایدن", "پنس", "ایالات متحده", "واشنگتن", "کاخ سفید"])
        text_has_zelensky = "زلنسکی" in norm

        if single == "🐀" and text_has_israel:
            return "🚨💩🐀🚨"
        if single == "🐒" and text_has_us:
            return "🚨🐒🐷🚨"
        if single == "🐴" and text_has_zelensky:
            return "🚨🐴🐴🚨"
        # اگر خبر خاص نبود، همان ایموجی را دوبار تکرار کن
        return f"🚨{single}{single}🚨"

    # دو یا بیشتر: دو تای اول را بردار
    return f"🚨{found[0]}{found[1]}🚨"

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
dest_entity = None

async def resolve_dest():
    global dest_entity
    try:
        dest_entity = await client.get_entity(DEST_CHANNEL)
        print(f"✅ کانال مقصد پیدا شد: {DEST_CHANNEL}")
    except Exception as e:
        print(f"❌ خطا در یافتن کانال مقصد: {e}")

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    try:
        msg = event.message
        text = msg.message or ""
        if not text.strip(): return

        if contains_blocked(text):
            print("⛔ تبلیغ"); return

        cleaned = clean_text(text)
        if is_rubbish(cleaned):
            print("⛔ بی‌ارزش"); return

        if is_duplicate(cleaned):
            print("⛔ تکراری"); return

        add_to_history(cleaned)

        header = generate_header(cleaned)
        final_text = f"{header}\n{cleaned}\n{MY_SIGNATURE}"

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
                print(f"⏳ FloodWait: {e.seconds}s"); await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"❌ خطای ارسال (تلاش {attempt+1}): {e}"); await asyncio.sleep(5)
        else:
            print("❌ ارسال پس از ۳ تلاش ناموفق ماند.")

        await asyncio.sleep(2)

    except Exception as e:
        print("❌ خطا:", e)

def memory_cleaner():
    while True:
        time.sleep(6 * 3600)
        if len(recent_hashes) > 200:
            del recent_hashes[:-200]
            print("🧹 حافظه پاکسازی شد.")

app = Flask(__name__)
@app.route("/")
def home(): return "YaraKhabar Bot is Running!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    if not SESSION_STRING:
        print("❌ SESSION_STRING تنظیم نشده.")
    else:
        threading.Thread(target=memory_cleaner, daemon=True).start()
        threading.Thread(target=run_web, daemon=True).start()
        print("🚀 ربات خبری هوشمند احسان با هدر پویا روشن شد...")
        with client:
            client.loop.run_until_complete(resolve_dest())
            client.run_until_disconnected()
