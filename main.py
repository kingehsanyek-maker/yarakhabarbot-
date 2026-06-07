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

# ===== شخصیت‌های سیاسی/نظامی (ایموجی پرچم کشور) =====
PERSON_EMOJI = {
    # ایران (۱۰۰ شخصیت)
    "پزشکیان": "🇮🇷", "مسعود پزشکیان": "🇮🇷",
    "عراقچی": "🇮🇷", "سید عباس عراقچی": "🇮🇷",
    "ظریف": "🇮🇷", "محمدجواد ظریف": "🇮🇷",
    "قالیباف": "🇮🇷", "محمدباقر قالیباف": "🇮🇷",
    "خامنه‌ای": "🇮🇷", "علی خامنه‌ای": "🇮🇷",
    "رئیسی": "🇮🇷", "ابراهیم رئیسی": "🇮🇷",
    "احمدی‌نژاد": "🇮🇷", "محمود احمدی‌نژاد": "🇮🇷",
    "روحانی": "🇮🇷", "حسن روحانی": "🇮🇷",
    "خاتمی": "🇮🇷", "سید محمد خاتمی": "🇮🇷",
    "لاریجانی": "🇮🇷", "علی لاریجانی": "🇮🇷",
    "آملی لاریجانی": "🇮🇷", "صادق آملی لاریجانی": "🇮🇷",
    "محسن رضایی": "🇮🇷", "سعید جلیلی": "🇮🇷",
    "علی‌اکبر ولایتی": "🇮🇷", "مصطفی پورمحمدی": "🇮🇷",
    "اسحاق جهانگیری": "🇮🇷", "عبدالناصر همتی": "🇮🇷",
    "محمدباقر نوبخت": "🇮🇷", "محمد نهاوندیان": "🇮🇷",
    "سید حسن خمینی": "🇮🇷", "اسماعیل بقائی": "🇮🇷",
    "حسین امیرعبداللهیان": "🇮🇷", "علی شمخانی": "🇮🇷",
    "محمد مخبر": "🇮🇷", "عزت‌الله ضرغامی": "🇮🇷",
    "غلامعلی حدادعادل": "🇮🇷", "غلامحسین محسنی اژه‌ای": "🇮🇷",
    "اکبر هاشمی رفسنجانی": "🇮🇷", "محسن هاشمی": "🇮🇷",
    "محمدرضا عارف": "🇮🇷", "علی مطهری": "🇮🇷",
    "احمد توکلی": "🇮🇷", "مصطفی معین": "🇮🇷",
    "علی‌اکبر ناطق نوری": "🇮🇷", "کمال خرازی": "🇮🇷",
    "محسن مهرعلیزاده": "🇮🇷", "محمدرضا باهنر": "🇮🇷",
    "علیرضا زاکانی": "🇮🇷", "پرویز فتاح": "🇮🇷",
    "علی ربیعی": "🇮🇷", "محمدرضا ظفرقندی": "🇮🇷",
    "بیژن نامدار زنگنه": "🇮🇷", "محمد اسلامی": "🇮🇷",
    "عباس آخوندی": "🇮🇷", "محمدجواد آذری جهرمی": "🇮🇷",
    "احمد وحیدی": "🇮🇷", "اسکندر مؤمنی": "🇮🇷",
    "علی عبدالعلی‌زاده": "🇮🇷", "جمیله علم‌الهدی": "🇮🇷",
    "سید ابراهیم رئیسی": "🇮🇷", "محمود علوی": "🇮🇷",
    "محمدجواد فدایی": "🇮🇷", "غلامرضا سلیمانی": "🇮🇷",
    "حسین سلامی": "🇮🇷", "محمدعلی جعفری": "🇮🇷",
    "قاسم سلیمانی": "🇮🇷", "اسماعیل قاآنی": "🇮🇷",
    "محمدباقر باقری": "🇮🇷", "امیرعلی حاجی‌زاده": "🇮🇷",
    "علی فدوی": "🇮🇷", "حسین دهقان": "🇮🇷",
    "محمدرضا آشتیانی": "🇮🇷", "امیر حاتمی": "🇮🇷",
    "مسعود جزایری": "🇮🇷", "ابوالفضل شکارچی": "🇮🇷",

    # آمریکا (۱۰ شخصیت)
    "ترامپ": "🇺🇸", "دونالد ترامپ": "🇺🇸",
    "بایدن": "🇺🇸", "جو بایدن": "🇺🇸",
    "پنس": "🇺🇸", "مایک پنس": "🇺🇸",
    "هریس": "🇺🇸", "کامالا هریس": "🇺🇸",
    "بلینکن": "🇺🇸", "آنتونی بلینکن": "🇺🇸",

    # اسرائیل (۵ شخصیت) ← ایموجی تمسخرآمیز
    "نتانیاهو": "🐀", "بنیامین نتانیاهو": "🐀",
    "گالانت": "🐀", "یوآو گالانت": "🐀",
    "اسحاق هرتزوگ": "🐀",

    # روسیه
    "پوتین": "🇷🇺", "ولادیمیر پوتین": "🇷🇺",
    "لاوروف": "🇷🇺", "سرگئی لاوروف": "🇷🇺",
    "مدودف": "🇷🇺", "دیمیتری مدودف": "🇷🇺",

    # چین
    "شی جین پینگ": "🇨🇳", "شی": "🇨🇳",
    "لی کیانگ": "🇨🇳", "وانگ یی": "🇨🇳",

    # اوکراین
    "زلنسکی": "🇺🇦", "ولودیمیر زلنسکی": "🇺🇦",
    "دیمیترو کولبا": "🇺🇦",

    # فرانسه
    "مکرون": "🇫🇷", "امانوئل مکرون": "🇫🇷",

    # انگلستان
    "بوریس جانسون": "🇬🇧", "ریشی سوناک": "🇬🇧", "شاه چارلز": "🇬🇧",

    # آلمان
    "شولتز": "🇩🇪", "اولاف شولتز": "🇩🇪",

    # ترکیه
    "اردوغان": "🇹🇷", "رجب طیب اردوغان": "🇹🇷",
    "چاووش‌اوغلو": "🇹🇷",

    # هند
    "نارندرا مودی": "🇮🇳", "مودی": "🇮🇳",

    # پاکستان
    "عمران خان": "🇵🇰", "شهباز شریف": "🇵🇰",

    # عراق
    "الکاظمی": "🇮🇶", "مصطفی الکاظمی": "🇮🇶",
    "صدر": "🇮🇶", "مقتدی صدر": "🇮🇶",

    # سایر
    "میشل عون": "🇱🇧", "عبدالفتاح السیسی": "🇪🇬",
    "اون": "🇱🇧", "السیسی": "🇪🇬",
}

# ===== کشورها و مکان‌ها (پرچم) =====
COUNTRY_EMOJI = {
    "ایران": "🇮🇷", "تهران": "🇮🇷",
    "آمریکا": "🇺🇸", "ایالات متحده": "🇺🇸", "واشنگتن": "🇺🇸",
    "اسرائیل": "🐀", "صهیونیست": "🐀", "تل‌آویو": "🐀",
    "روسیه": "🇷🇺", "مسکو": "🇷🇺", "کرملین": "🇷🇺",
    "چین": "🇨🇳", "پکن": "🇨🇳",
    "اوکراین": "🇺🇦", "کیف": "🇺🇦",
    "فرانسه": "🇫🇷", "پاریس": "🇫🇷",
    "انگلیس": "🇬🇧", "بریتانیا": "🇬🇧", "لندن": "🇬🇧",
    "آلمان": "🇩🇪", "برلین": "🇩🇪",
    "ترکیه": "🇹🇷", "آنکارا": "🇹🇷",
    "هند": "🇮🇳", "دهلی": "🇮🇳",
    "پاکستان": "🇵🇰", "اسلام‌آباد": "🇵🇰",
    "عراق": "🇮🇶", "بغداد": "🇮🇶",
    "سوریه": "🇸🇾", "دمشق": "🇸🇾",
    "لبنان": "🇱🇧", "بیروت": "🇱🇧",
    "یمن": "🇾🇪", "صنعا": "🇾🇪",
    "فلسطین": "🇵🇸", "غزه": "🇵🇸",
    "عربستان": "🇸🇦", "ریاض": "🇸🇦",
    "امارات": "🇦🇪", "ابوظبی": "🇦🇪",
    "قطر": "🇶🇦", "دوحه": "🇶🇦",
    "کویت": "🇰🇼", "بحرین": "🇧🇭",
    "عمان": "🇴🇲", "اردن": "🇯🇴",
    "جمهوری آذربایجان": "🇦🇿", "باکو": "🇦🇿",
    "ارمنستان": "🇦🇲", "ایروان": "🇦🇲",
    "گرجستان": "🇬🇪", "تفلیس": "🇬🇪",
    "افغانستان": "🇦🇫", "کابل": "🇦🇫",
}

# ===== موضوعات و کلمات نظامی (با اولویت بالا) =====
TOPIC_EMOJI = {
    # نظامی (برای رفع ابهام با "کشتی" ورزشی)
    "کشتی تجاری": "🚢", "ناو": "🚢", "ناوشکن": "🚢",
    "زیردریایی": "🚢", "شناور": "🚢", "نیروی دریایی": "🚢",
    "هواپیما": "✈️", "جنگنده": "✈️", "فانتوم": "✈️",
    "اف-۳۵": "✈️", "سوخو": "✈️", "میگ": "✈️", "رافال": "✈️",
    "پهپاد": "🛸", "موشک": "🚀", "پدافند": "🛡️",
    "رادار": "📡", "رزمایش": "🎖️", "ارتش": "🎖️",
    "سپاه": "🎖️", "نیروی هوایی": "✈️",
    "جنگ": "⚔️", "حمله": "💣", "بمب": "💣", "انفجار": "💥",
    "ترور": "🔫", "گروگان": "🔒",

    # ورزش (فقط وقتی قرینه‌های ورزشی باشند)
    "کشتی آزاد": "🤼", "کشتی فرنگی": "🤼", "وزن کشتی": "🤼",
    "رقابت‌های کشتی": "🤼", "تیم ملی کشتی": "🤼",
    "فوتبال": "⚽", "والیبال": "🏐", "بسکتبال": "🏀",
    "ورزش": "🏅", "المپیک": "🏟️", "تنیس": "🎾",
    "شنا": "🏊", "وزنه‌برداری": "🏋️", "بوکس": "🥊",
    "طلایی": "🥇", "نقره": "🥈", "برنز": "🥉",

    # دیپلماسی
    "مذاکره": "🤝", "توافق": "📝", "معاهده": "🕊️",
    "دیدار": "🤝", "نشست": "👥", "سفر": "✈️",

    # اقتصاد و انرژی
    "اقتصاد": "💰", "نفت": "🛢️", "گاز": "🔥", "بورس": "📈",
    "تورم": "📉", "دلار": "💵", "ارز": "💱", "تحریم": "🚫",

    # حوادث طبیعی
    "زلزله": "🌍", "سیل": "🌊", "طوفان": "🌀", "آتش‌سوزی": "🔥",

    # سلامت
    "کرونا": "😷", "واکسن": "💉", "بیمارستان": "🏥", "پزشکی": "🩺",

    # سایر
    "انتخابات": "🗳️", "اعتراض": "✊", "تظاهرات": "🚩",
    "فرهنگ": "🎭", "هنر": "🎨", "سینما": "🎬", "موسیقی": "🎵",
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

    # ۱. جستجوی شخصیت‌های معروف (اولویت بالاتر)
    for person, emoji in PERSON_EMOJI.items():
        if person in norm and emoji not in countries:
            countries.append(emoji)

    # ۲. جستجوی کشورها و مکان‌ها
    for country, emoji in COUNTRY_EMOJI.items():
        if country in norm and emoji not in countries:
            countries.append(emoji)

    # ۳. جستجوی موضوعات
    for topic, emoji in TOPIC_EMOJI.items():
        if topic in norm and emoji not in topics:
            topics.append(emoji)

    # اگر "کشتی" بدون قرینهٔ ورزشی بود، 🚢 بده
    if "کشتی" in norm and "🤼" not in topics:
        topics.insert(0, "🚢")

    # ساخت header با ۳ ایموجی
    final = []
    if countries:
        final.append(countries[0])
    if topics:
        final.append(topics[0])
    if len(countries) > 1:
        final.append(countries[1])
    elif len(topics) > 1:
        final.append(topics[1])
    else:
        pass

    while len(final) < 3:
        for d in DEFAULT_EMOJIS:
            if d not in final:
                final.append(d)
                break

    return f"🚨{final[0]}{final[1]}{final[2]}🚨"

def format_news(cleaned_text):
    lines = cleaned_text.split('\n', 1)
    if lines:
        title = f"**{lines[0].strip()}**"
        rest = lines[1].strip() if len(lines) > 1 else ""
        return f"{title}\n{rest}" if rest else title
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
        final_text = f"{header}\n{formatted_body}{MY_SIGNATURE}"

        global dest_entity
        for attempt in range(3):
            try:
                if dest_entity is None:
                    await resolve_dest()
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
            except Exception:
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
        print("🚀 ربات خبری هوشمند با تشخیص شخصیت‌ها روشن شد...")
        with client:
            client.loop.run_until_complete(resolve_dest())
            client.run_until_disconnected()
