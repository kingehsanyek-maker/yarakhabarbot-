import os, time, asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from flask import Flask
import threading, difflib, re

# ===== تنظیمات =====
API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"
SESSION_STRING = os.environ.get("SESSION_STRING", "")

SOURCE_CHANNELS = ["KhabarFori", "KhabarFooury", "akharinkhabar", "Projectmeshkat"]
DEST_CHANNEL = "@yarakhabar"
MY_SIGNATURE = "\n@YARAKHABAR📢\n🔷🔹🎯هر لحظه یک خبر تازه🎯🔹🔷"

# ===== کلمات کلیدی کشورها / مقامات =====
COUNTRY_EMOJI = {
    # اسرائیل (استثنا: موش می‌ماند)
    "اسرائیل": "🐀", "نتانیاهو": "🐀", "صهیونیست": "🐀",
    "تل‌آویو": "🐀", "موساد": "🐀", "فلسطین اشغالی": "🐀",
    # بقیهٔ جهان (همه پرچم یا نماد محترمانه)
    "آمریکا": "🇺🇸", "ایالات متحده": "🇺🇸", "واشنگتن": "🇺🇸",
    "ترامپ": "🇺🇸", "بایدن": "🇺🇸", "کاخ سفید": "🇺🇸",
    "روسیه": "🇷🇺", "پوتین": "🇷🇺", "مسکو": "🇷🇺", "کرملین": "🇷🇺",
    "چین": "🇨🇳", "شی جین پینگ": "🇨🇳", "پکن": "🇨🇳",
    "ایران": "🇮🇷", "تهران": "🇮🇷", "سپاه": "🇮🇷", "بسیج": "🇮🇷",
    "فرانسه": "🇫🇷", "مکرون": "🇫🇷", "پاریس": "🇫🇷",
    "انگلیس": "🇬🇧", "بریتانیا": "🇬🇧", "لندن": "🇬🇧", "بوریس جانسون": "🇬🇧",
    "آلمان": "🇩🇪", "برلین": "🇩🇪", "شولتز": "🇩🇪",
    "اوکراین": "🇺🇦", "کیف": "🇺🇦", "زلنسکی": "🇺🇦",
    "هند": "🇮🇳", "پاکستان": "🇵🇰", "افغانستان": "🇦🇫",
    "ترکیه": "🇹🇷", "عربستان": "🇸🇦", "امارات": "🇦🇪",
    "ژاپن": "🇯🇵", "کره جنوبی": "🇰🇷", "کره شمالی": "🇰🇵",
    "برزیل": "🇧🇷", "عراق": "🇮🇶", "سوریه": "🇸🇾",
    "یمن": "🇾🇪", "لبنان": "🇱🇧", "فلسطین": "🇵🇸",
    "مصر": "🇪🇬", "لیبی": "🇱🇾", "تونس": "🇹🇳",
    "کانادا": "🇨🇦", "استرالیا": "🇦🇺", "ایتالیا": "🇮🇹",
    "اسپانیا": "🇪🇸", "هلند": "🇳🇱", "بلژیک": "🇧🇪",
    "سوئد": "🇸🇪", "نروژ": "🇳🇴", "دانمارک": "🇩🇰",
    "یونان": "🇬🇷", "اتریش": "🇦🇹", "سوئیس": "🇨🇭",
    "قطر": "🇶🇦", "کویت": "🇰🇼", "بحرین": "🇧🇭",
    "عمان": "🇴🇲", "اردن": "🇯🇴", "جمهوری آذربایجان": "🇦🇿",
    "ارمنستان": "🇦🇲", "گرجستان": "🇬🇪", "قزاقستان": "🇰🇿",
    # سازمان‌ها
    "ناتو": "🛡️", "سازمان ملل": "🇺🇳", "اتحادیه اروپا": "🇪🇺",
}

# ===== کلمات کلیدی موضوعات =====
TOPIC_EMOJI = {
    # ورزش
    "فوتبال": "⚽", "والیبال": "🏐", "کشتی": "🤼", "بسکتبال": "🏀",
    "ورزش": "🏅", "المپیک": "🏟️", "تنیس": "🎾", "شنا": "🏊",
    "دوچرخه‌سواری": "🚴", "وزنه‌برداری": "🏋️", "بوکس": "🥊",
    "طلایی": "🥇", "نقره": "🥈", "برنز": "🥉",
    # نظامی و بحران
    "جنگ": "⚔️", "حمله": "💣", "موشک": "🚀", "پدافند": "🛡️",
    "هسته‌ای": "☢️", "شیمیایی": "🧪", "پهپاد": "🛸",
    "زلزله": "🌍", "سیل": "🌊", "طوفان": "🌀", "آتش‌سوزی": "🔥",
    "انفجار": "💥", "بمب": "💣", "گروگان": "🔒", "ترور": "🔫",
    # اقتصاد و انرژی
    "اقتصاد": "💰", "نفت": "🛢️", "گاز": "🔥", "بورس": "📈",
    "تورم": "📉", "دلار": "💵", "یورو": "💶", "ارز": "💱",
    "تحریم": "🚫", "صادرات": "📦", "واردات": "📥",
    # دیپلماسی و سیاست
    "انتخابات": "🗳️", "رئیس‌جمهور": "🎩", "نخست‌وزیر": "👔",
    "دولت": "🏛️", "مجلس": "🏛️", "قانون": "📜",
    "مذاکره": "🤝", "توافق": "📝", "معاهده": "🕊️",
    "سفر": "✈️", "دیدار": "🤝", "نشست": "👥",
    "اعتراض": "✊", "تظاهرات": "🚩",
    # سلامت و فناوری
    "کرونا": "😷", "واکسن": "💉", "بیمارستان": "🏥",
    "پزشکی": "🩺", "هوش مصنوعی": "🤖", "فضا": "🚀",
    "اینترنت": "🌐", "ماهواره": "🛰️",
    # حوادث
    "تصادف": "🚗", "سقوط هواپیما": "✈️", "ریزش ساختمان": "🏚️", "غرق": "🚢",
    # فرهنگ و هنر
    "فرهنگ": "🎭", "هنر": "🎨", "سینما": "🎬", "موسیقی": "🎵",
    "دانشگاه": "🎓", "مدرسه": "🏫",
}

DEFAULT_EMOJIS = ("🌟", "❇️", "✨")

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

recent_texts = []
MAX_HISTORY = 200

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

def is_similar(new_text, threshold=0.8):
    for old_text in recent_texts:
        similarity = difflib.SequenceMatcher(None, new_text, old_text).ratio()
        if similarity >= threshold:
            return True
    return False

def add_to_history(text):
    recent_texts.append(text)
    if len(recent_texts) > MAX_HISTORY:
        recent_texts.pop(0)

def generate_header(text):
    norm = normalize(text).lower()
    countries = []
    topics = []

    # جمع‌آوری کشورها
    for keyword, emoji in COUNTRY_EMOJI.items():
        if keyword in norm and emoji not in countries:
            countries.append(emoji)

    # جمع‌آوری موضوعات
    for keyword, emoji in TOPIC_EMOJI.items():
        if keyword in norm and emoji not in topics:
            topics.append(emoji)

    # ساخت لیست نهایی ۳ تایی
    final = []
    # ۱. کشور اول (اگر هست)
    if countries:
        final.append(countries[0])
    # ۲. موضوع اول (اگر هست)
    if topics:
        final.append(topics[0])
    # ۳. کشور دوم (اگر هست) وگرنه موضوع دوم (اگر هست) وگرنه ایموجی پیش‌فرض
    if len(countries) > 1:
        final.append(countries[1])
    elif len(topics) > 1:
        final.append(topics[1])
    else:
        # هنوز جا داریم، با پیش‌فرض‌ها پر می‌کنیم
        pass

    # پر کردن تا ۳ ایموجی
    while len(final) < 3:
        for d in DEFAULT_EMOJIS:
            if d not in final:
                final.append(d)
                break

    return f"🚨{final[0]}{final[1]}{final[2]}🚨"

def format_news(cleaned_text):
    """اولین خط (تیتر) را بولد و متن را جدا می‌کند"""
    lines = cleaned_text.split('\n', 1)
    if len(lines) >= 1:
        # تیتر (خط اول) را بولد می‌کنیم
        title = f"**{lines[0].strip()}**"
        # بقیهٔ متن
        rest = lines[1].strip() if len(lines) > 1 else ""
        if rest:
            return f"{title}\n{rest}"
        else:
            return title
    return cleaned_text

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

        if is_similar(cleaned):
            print("⛔ تکراری"); return

        add_to_history(cleaned)

        header = generate_header(cleaned)
        formatted_body = format_news(cleaned)
        # ساختار نهایی: header + متن بولدشده + امضا
        final_text = f"{header}\n{formatted_body}{MY_SIGNATURE}"

        global dest_entity
        for attempt in range(3):
            try:
                if dest_entity is None:
                    await resolve_dest()
                # ارسال با Markdown (برای فعال شدن **بولد**)
                if msg.media:
                    await client.send_message(
                        dest_entity or DEST_CHANNEL,
                        final_text,
                        file=msg.media,
                        parse_mode='md'
                    )
                else:
                    await client.send_message(
                        dest_entity or DEST_CHANNEL,
                        final_text,
                        parse_mode='md'
                    )
                print("✅ ارسال شد")
                break
            except FloodWaitError as e:
                print(f"⏳ FloodWait: {e.seconds}s"); await asyncio.sleep(e.seconds)
            except Exception as e:
                # اگر parse_mode خطا داد (مثلاً کاراکترهای رزرو شده Markdown)،
                # بدون parse_mode دوباره تلاش کن
                try:
                    if msg.media:
                        await client.send_message(dest_entity or DEST_CHANNEL, final_text, file=msg.media)
                    else:
                        await client.send_message(dest_entity or DEST_CHANNEL, final_text)
                    print("✅ ارسال شد (بدون Markdown)")
                    break
                except Exception as e2:
                    print(f"❌ خطای ارسال (تلاش {attempt+1}): {e2}")
                await asyncio.sleep(5)
        else:
            print("❌ ارسال پس از ۳ تلاش ناموفق ماند.")

        await asyncio.sleep(2)

    except Exception as e:
        print("❌ خطا:", e)

def memory_cleaner():
    while True:
        time.sleep(6 * 3600)
        if len(recent_texts) > 200:
            del recent_texts[:-200]
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
        print("🚀 ربات حرفه‌ای احسان (تیتر بولد + سه ایموجی) روشن شد...")
        with client:
            client.loop.run_until_complete(resolve_dest())
            client.run_until_disconnected()
