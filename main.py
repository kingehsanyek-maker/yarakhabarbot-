import os, time, asyncio, re, difflib, threading
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from flask import Flask

# ===== تنظیمات =====
API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"
SESSION_STRING = os.environ.get("SESSION_STRING", "")

SOURCE_CHANNELS = ["akharinkhabar", "Projectmeshkat"]
DEST_CHANNEL = "@yarakhabar"
MY_SIGNATURE = "\n@YARAKHABAR📢\n🔷🔹🎯هر لحظه یک خبر تازه🎯🔹🔷"

# ===== لیست‌های واژگان (کامل) =====
PERSONS = { ... }  # کامل
PLACES = { ... }   # کامل
MILITARY = { ... } # کامل
SPORTS_CONTEXT = [ ... ] # کامل
TOPICS = { ... }   # کامل
EXTRA_TOPICS = { ... } # کامل

DEFAULT_EMOJIS = ("🌟", "❇️", "✨")

# ===== لیست سیاه کلمات ممنوعه (برای بلاک کامل پیام) =====
BLOCKED_WORDS = [
    "تبلیغ", "خرید", "فروش", "کسب درآمد", "عضویت", "ارزان", "تخفیف",
    "ویژه", "همین الان", "کلیک کن", "دانلود", "فیلترشکن", "vpn",
    "سرعت عالی", "امنیت بالا", "اتصال پایدار", "فروشی", "مفت", "حراج",
    "ارزون", "ثبت نام", "رایگان", "شرط‌بندی", "شرط بندی", "bet",
    "کازینو", "قمار", "پیش‌بینی ورزشی", "برد تضمینی", "استروئید",
    "فیلم سوپر", "عکس خصوصی", "همسریابی", "دوستیابی",
    # خیریه و کمک مالی (کلاهبرداری)
    "خیریه", "خیریه نیک", "شماره کارت", "شبا", "واریز", "کمک مالی",
    "پرونده بیمار", "مجوزها", "تسویه", "مازاد کمک", "تلگرام نیک",
    "سایت خیریه", "PoshtibaniDarman", "کودکان محروم",
    "داروهای گران", "بازار آزاد", "چشم انتظار همت", "در توان مادر",
    "پرونده‌های درمان", "گزارش پرونده", "مازاد کمک‌ها",
    "صرف امورات مؤسسه", "مؤسسه خیریه", "نیازمند", "هزینه درمان",
    "کودک بیمار", "انجمن", "کمک مردمی", "پرداخت امن",
    "درگاه پرداخت", "زرین پال", "idpay", "بله، پرداخت",
]

# ===== لیست امضاها و تبلیغات برای پاک‌سازی (نه بلاک) =====
TEXTS_TO_REMOVE = [
    "@akharinkhabar", "@Akharinkhabar", "@AKHARINKHABAR",
    "akharinkhabar", "Akharinkhabar", "AKHARINKHABAR",
    "| akharinkhabar.ir", "akharinkhabar.ir",
    "t.me/akharinkhabar", "https://t.me/akharinkhabar",
    "@Projectmeshkat", "t.me/Projectmeshkat",
    "https://zil.ink/ProjectMeshkat",
    "آخرین خبر در روبیکا", "آخرین خبر در ایتا", "آخرین خبر در بله",
    "آخرین خبر در سروش", "آخرین خبر در گپ",
    "سایت آخرین خبر", "اپلیکیشن آخرین خبر",
]

recent_texts = []
MAX_HISTORY = 200

def normalize(text):
    if not text: return ""
    text = text.replace("\u200c", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")
    return re.sub(r"\s+", " ", text).strip()

def remove_promotional_links(text):
    """
    حذف کامل خطوطی که شامل لینک به پیام‌رسان‌های ایرانی یا خارجی هستند.
    همچنین اگر خط قبلی فقط نام آن پیام‌رسان باشد و خط بعدی لینک داشته باشد،
    هر دو خط حذف می‌شوند.
    """
    lines = text.split('\n')
    # دامنه‌های هدف (حتی بدون پروتکل)
    promo_domains = [
        'rubika.ir', 'eitaa.com', 'ble.ir', 'splus.ir', 'gap.im',
        't.me', 'telegram.me', 'instagram.com'
    ]
    
    # الگو: خطی که شامل یکی از دامنه‌ها باشد (با یا بدون https://)
    link_pattern = re.compile(
        r'(?:https?://)?(?:www\.)?(?:' + '|'.join(re.escape(d) for d in promo_domains) + r')\S*',
        re.IGNORECASE
    )

    # کلمات کلیدی که ممکن است قبل از لینک بیایند (اگر در خط جداگانه باشند)
    trigger_words = ['روبیکا', 'ایتا', 'بله', 'سروش', 'گپ', 'تلگرام', 'اینستاگرام']

    filtered_lines = []
    skip_next = False
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue

        # اگر خط جاری شامل لینک تبلیغاتی است، کلاً حذف شود
        if link_pattern.search(line):
            continue

        # اگر خط جاری یکی از کلمات کلیدی است و خط بعدی لینک دارد، هر دو حذف
        stripped = line.strip()
        is_trigger = any(
            re.fullmatch(rf'{re.escape(w)}\s*👇?', stripped, re.IGNORECASE) or
            stripped.lower() == w.lower()
            for w in trigger_words
        )
        if is_trigger and i+1 < len(lines) and link_pattern.search(lines[i+1]):
            skip_next = True
            continue

        filtered_lines.append(line)

    return '\n'.join(filtered_lines)

def clean_text(text):
    if not text: return ""
    # ۱. حذف لینک‌های تبلیغاتی (پیام‌رسان‌ها)
    text = remove_promotional_links(text)
    # ۲. حذف سایر لینک‌ها
    text = re.sub(r"https?://\S+", "", text)
    # ۳. حذف دامنه‌های .ir که ممکن است باقی مانده باشند
    text = re.sub(r"\S*\.ir\S*", "", text)
    # ۴. حذف امضاهای مشخص
    for item in TEXTS_TO_REMOVE:
        text = text.replace(item, "")
    # ۵. حذف منشن‌ها
    text = re.sub(r"@[^\s]+", "", text)
    # ۶. حذف خط‌های خالی اضافی
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()

def is_rubbish(text):
    return not text or len(text.strip()) < 6

def contains_blocked(text):
    norm = normalize(text).lower()
    for bad in BLOCKED_WORDS:
        if bad.lower() in norm:
            return True
    return False

def has_financial_scam(text):
    if re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', text):
        return True
    if re.search(r'\bIR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', text, re.IGNORECASE):
        return True
    if re.search(r'(pay|zarinpal|idpay|payment|شارژ|کیف پول)', text, re.IGNORECASE):
        return True
    return False

def is_similar(new_text, threshold=0.8):
    for old_text in recent_texts:
        if difflib.SequenceMatcher(None, new_text, old_text).ratio() >= threshold:
            return True
    return False

def add_to_history(text):
    recent_texts.append(text)
    if len(recent_texts) > MAX_HISTORY:
        recent_texts.pop(0)

def tokenize(text):
    return re.findall(r'\w+', normalize(text))

def generate_header(text):
    tokens = tokenize(text)
    text_lower = normalize(text).lower()
    has_sports = any(ctx in text_lower for ctx in SPORTS_CONTEXT)

    countries = []
    topics = []

    for token in tokens:
        if token in PERSONS:
            emoji = PERSONS[token]
            if emoji not in countries:
                countries.append(emoji)

    for token in tokens:
        if token in PLACES:
            emoji = PLACES[token]
            if emoji not in countries:
                countries.append(emoji)

    for token in tokens:
        if token in MILITARY:
            if token == "کشتی" and has_sports:
                continue
            emoji = MILITARY[token]
            if emoji not in topics:
                topics.append(emoji)

    for token in tokens:
        if token in TOPICS:
            emoji = TOPICS[token]
            if emoji not in topics:
                topics.append(emoji)
        if token in EXTRA_TOPICS:
            for e in list(EXTRA_TOPICS[token]):
                if e not in topics:
                    topics.append(e)

    uniq_countries = []
    for c in countries:
        if c not in uniq_countries:
            uniq_countries.append(c)
    uniq_topics = []
    for t in topics:
        if t not in uniq_topics:
            uniq_topics.append(t)

    final = []
    if uniq_countries:
        final.append(uniq_countries[0])
    if uniq_topics:
        final.append(uniq_topics[0])
    if len(uniq_countries) > 1:
        final.append(uniq_countries[1])
    elif len(uniq_topics) > 1:
        final.append(uniq_topics[1])
    else:
        for d in DEFAULT_EMOJIS:
            if d not in final:
                final.append(d)
                break

    while len(final) < 3:
        for d in DEFAULT_EMOJIS:
            if d not in final:
                final.append(d)
                break

    return f"🚨{final[0]}{final[1]}{final[2]}🚨"

def format_news(cleaned_text):
    lines = cleaned_text.split('\n', 1)
    if not lines: return cleaned_text
    title = f"**{lines[0].strip()}**"
    rest = lines[1].strip() if len(lines) > 1 else ""
    return f"{title}\n{rest}" if rest else title

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

        # فیلترهای دفاعی برای بلاک کامل (تبلیغات، کلاهبرداری)
        if contains_blocked(text) or has_financial_scam(text):
            print("⛔ تبلیغ / کلاهبرداری")
            return

        cleaned = clean_text(text)  # اینجا لینک‌های پیام‌رسان‌ها پاک می‌شوند
        if is_rubbish(cleaned):
            print("⛔ بی‌ارزش")
            return

        if is_similar(cleaned):
            print("⛔ تکراری")
            return

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
                    await client.send_message(dest_entity or DEST_CHANNEL, final_text, file=msg.media, parse_mode='md')
                else:
                    await client.send_message(dest_entity or DEST_CHANNEL, final_text, parse_mode='md')
                print("✅ ارسال شد")
                break
            except FloodWaitError as e:
                print(f"⏳ FloodWait: {e.seconds}s"); await asyncio.sleep(e.seconds)
            except Exception as e:
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
        print("🚀 ربات هوشمند پاک‌کنندهٔ لینک‌های تبلیغاتی روشن شد.")
        with client:
            client.loop.run_until_complete(resolve_dest())
            client.run_until_disconnected()
