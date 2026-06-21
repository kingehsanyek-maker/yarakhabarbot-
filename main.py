import os, time, asyncio, re, difflib, threading, hashlib
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from flask import Flask

# ===== تنظیمات =====
API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"
SESSION_STRING = os.environ.get("SESSION_STRING", "")

SOURCE_CHANNELS = ["irna_1313", "isna94", "Projectmeshkat"]
DEST_CHANNEL = "@yarakhabar"
MY_SIGNATURE = "\n\n@YARAKHABAR📢\n🎯👈 هر لحظه یک خبر تازه 👉🎯"

# ===== لیست‌های واژگان کامل =====
PERSONS = {
    "پزشکیان": "🇮🇷", "مسعود پزشکیان": "🇮🇷", "عراقچی": "🇮🇷",
    "سید عباس عراقچی": "🇮🇷", "ظریف": "🇮🇷", "محمدجواد ظریف": "🇮🇷",
    "قالیباف": "🇮🇷", "محمدباقر قالیباف": "🇮🇷", "خامنه‌ای": "🇮🇷",
    "علی خامنه‌ای": "🇮🇷", "آیت‌الله خامنه‌ای": "🇮🇷",
    "رئیسی": "🇮🇷", "ابراهیم رئیسی": "🇮🇷",
    "احمدی‌نژاد": "🇮🇷", "محمود احمدی‌نژاد": "🇮🇷",
    "روحانی": "🇮🇷", "حسن روحانی": "🇮٬", "خاتمی": "🇮🇷",
    "سید محمد خاتمی": "🇮🇷", "لاریجانی": "🇮🇷", "علی لاریجانی": "🇮🇷",
    "آملی لاریجانی": "🇮🇷", "صادق آملی لاریجانی": "🇮٬",
    "محسن رضایی": "🇮🇷", "سعید جلیلی": "🇮🇷",
    "علی‌اکبر ولایتی": "🇮🇷", "مصطفی پورمحمدی": "🇮🇷",
    "اسحاق جهانگیری": "🇮🇷", "عبدالناصر همتی": "🇮🇷",
    "محمدباقر نوبخت": "🇮🇷", "محمد نهاوندیان": "🇮🇷",
    "سید حسن خمینی": "🇮🇷", "اسماعیل بقائی": "🇮🇷",
    "حسین امیرعبداللهیان": "🇮🇷", "علی شمخانی": "🇮٬",
    "محمد مخبر": "🇮🇷", "عزت‌الله ضرغامی": "🇮🇷",
    "غلامعلی حدادعادل": "🇮🇷", "غلامحسین محسنی اژه‌ای": "🇮🇷",
    "اکبر هاشمی رفسنجانی": "🇮🇷", "محسن هاشمی": "🇮🇷",
    "محمدرضا عارف": "🇮🇷", "علی مطهری": "🇮🇷",
    "احمد توکلی": "🇮🇷", "مصطفی معین": "🇮🇷",
    "علی‌اکبر ناطق نوری": "🇮🇷", "کمال خرازی": "🇮٬",
    "محسن مهرعلیزاده": "🇮🇷", "محمدرضا باهنر": "🇮🇷",
    "علیرضا زاکانی": "🇮🇷", "پرویز فتاح": "🇮🇷",
    "محمد اسلامی": "🇮🇷", "عباس آخوندی": "🇮🇷",
    "محمدجواد آذری جهرمی": "🇮🇷", "احمد وحیدی": "🇮٬",
    "اسکندر مؤمنی": "🇮🇷", "علی عبدالعلی‌زاده": "🇮🇷",
    "مهدی طباطبایی": "🇮🇷", "هادی خانی": "🇮🇷",
    "بادامچیان": "🇮🇷", "ضرغامی": "🇮🇷",
    "زیدآبادی": "🇮🇷", "علم‌الهدی": "🇮🇷",
    "ابوترابی‌فرد": "🇮🇷", "آیت‌الله سبحانی": "🇮🇷",
    "ترامپ": "🇺🇸", "دونالد ترامپ": "🇺🇸",
    "بایدن": "🇺🇸", "جو بایدن": "🇺🇸",
    "پنس": "🇺🇸", "هریس": "🇺٬", "کامالا هریس": "🇺٬",
    "بوش": "🇺🇸", "اوباما": "🇺٬", "باراک اوباما": "🇺٬",
    "کلینتون": "🇺🇸", "مایک پمپئو": "🇺٬",
    "جان کری": "🇺٬", "بلینکن": "🇺٬", "آنتونی بلینکن": "🇺٬",
    "ونس": "🇺🇸", "جی‌دی ونس": "🇺٬",
    "نتانیاهو": "🐀", "بنیامین نتانیاهو": "🐀",
    "صهیونیست": "🐀", "موساد": "🐀",
    "بن‌گویر": "🐀", "ایتمار بن‌گویر": "🐀",
    "شیخ نعیم قاسم": "🇱🇧", "نعیم قاسم": "🇱🇧",
    "جوزف عون": "🇱🇧", "نواف سلام": "🇱🇧",
    "زلنسکی": "🇺🇦", "ولودیمیر زلنسکی": "🇺🇦",
    "لاوروف": "🇷🇺", "سرگئی لاوروف": "🇷🇺",
    "شهباز شریف": "🇵🇰", "محمد اسحاق دار": "🇵🇰",
    "مکرون": "🇫🇷", "امانوئل مکرون": "🇫🇷",
    "مرتس": "🇩🇪", "فریدریش مرتس": "🇩٪",
}

PLACES = {
    "تهران": "🇮🇷", "اصفهان": "🇮🇷", "تبریز": "🇮🇷", "مشهد": "🇮🇷",
    "بندرعباس": "🇮🇷", "خارک": "🇮🇷", "چابهار": "🇮٬", "بوشهر": "🇮🇷",
    "عسلویه": "🇮🇷", "اهواز": "🇮🇷", "خوزستان": "🇮🇷", "کیش": "🇮🇷",
    "قشم": "🇮🇷", "تنگه هرمز": "🇮🇷", "ابوموسی": "🇮🇷",
    "تنب بزرگ": "🇮🇷", "تنب کوچک": "🇮🇷",
    "شهران": "🇮🇷", "همت": "🇮🇷", "خاش": "🇮🇷", "زهک": "🇮٬",
    "میناب": "🇮🇷", "کرمان": "🇮🇷", "یزد": "🇮🇷", "شیراز": "🇮🇷",
    "فرودگاه امام": "🇮🇷", "شهر فرودگاهی امام": "🇮🇷",
    "بیروت": "🇱🇧", "ضاحیه": "🇱🇧", "صور": "🇱🇧", "صیدا": "🇱🇧",
    "بقاع": "🇱🇧", "نبطیه": "🇱٬", "بعلبک": "🇱🇧",
    "دمشق": "🇸🇾", "حلب": "🇸🇾", "حمص": "🇸🇾", "لاذقیه": "🇸🇾",
    "طرطوس": "🇸🇾", "ادلب": "🇸🇾", "دیرالزور": "🇸🇾", "قنیطره": "🇸🇾",
    "غزه": "🇵🇸", "رفح": "🇵🇸", "خان یونس": "🇵٬",
    "جبالیا": "🇵🇸", "بیت لاهیا": "🇵🇸", "نوار غزه": "🇵🇸",
    "جنین": "🇵🇸", "طولکرم": "🇵🇸", "نابلس": "🇵🇸",
    "رام‌الله": "🇵🇸", "الخلیل": "🇵🇸", "بیت لحم": "🇵🇸",
    "اریحا": "🇵٬", "کرانه باختری": "🇵٬", "مسجدالاقصی": "🇵🇸",
    "الاقصی": "🇵🇸", "بیت حانون": "🇵🇸", "دیرالبلح": "🇵🇸",
    "بیت جالا": "🇵🇸", "بیت ساحور": "🇵٬", "قلقیلیه": "🇵٬",
    "تل‌آویو": "🇮🇱", "قدس": "🇮🇱", "حیفا": "🇮🇱",
    "اشدود": "🇮🇱", "بئرالسبع": "🇮🇱", "الجلیل": "🇮٬",
    "ایلات": "🇮🇱", "نتانیا": "🇮🇱", "هرتزلیا": "🇮🇱",
    "صنعا": "🇾🇪", "الحدیده": "🇾🇪", "صعده": "🇾🇪", "عدن": "🇾٪",
    "باب المندب": "🇾🇪",
    "بغداد": "🇮🇶", "بصره": "🇮🇶", "اربیل": "🇮🇶",
    "موصل": "🇮🇶", "کرکوک": "🇮🇶", "نجف": "🇮🇶", "کربلا": "🇮🇶",
    "ریاض": "🇸🇦", "جده": "🇸🇦", "ینبع": "🇸🇦", "مکه": "🇸٬", "مدینه": "🇸🇦",
    "دبی": "🇦🇪", "ابوظبی": "🇦🇪", "شارجه": "🇦٬",
    "دوحه": "🇶🇦", "لوسیل": "🇶🇦",
    "کویت": "🇰🇼",
    "منامه": "🇧🇭",
    "مسقط": "🇴🇲",
    "آنکارا": "🇹🇷", "استانبول": "🇹٬",
    "مسکو": "🇷🇺", "سن پترزبورگ": "🇷🇺",
    "کی‌یف": "🇺🇦",
    "واشنگتن": "🇺🇸", "نیویورک": "🇺٬", "پنتاگون": "🇺٬",
    "کاخ سفید": "🇺🇸", "فلوریدا": "🇺٬", "لس آنجلس": "🇺٬",
    "پکن": "🇨🇳", "شانگهای": "🇨٬",
    "لندن": "🇬🇧", "پاریس": "🇫🇷", "برلین": "🇩🇪", "بروکسل": "🇧🇪",
    "سوئیس": "🇨🇭", "بورگن‌اشتاک": "🇨🇭",
    "قاهره": "🇪🇬", "اسکندریه": "🇪🇬", "کانال سوئز": "🇪٬",
    "خلیج فارس": "🌊", "دریای عمان": "🌊", "دریای سرخ": "🌊",
    "اقیانوس هند": "🌊", "مدیترانه": "🌊", "خلیج عدن": "🌊",
    "تنگه هرمز": "🌊",
}

MILITARY = {
    "ناو": "🚢", "ناوشکن": "🚢", "زیردریایی": "🚢", "شناور": "🚢",
    "هواپیما": "✈️", "جنگنده": "✈️", "فانتوم": "✈️", "اف-35": "✈️",
    "سوخو": "✈️", "میگ": "✈️", "رافال": "✈️", "پهپاد": "✈️",
    "موشک": "🚀", "پدافند": "🛡️", "رادار": "📡",
    "رزمایش": "🎖️", "ارتش": "🎖️", "سپاه": "🎖️",
    "نیروی دریایی": "🚢", "نیروی هوایی": "✈️", "تانک": "💥",
}

SPORTS_CONTEXT = [
    "فوتبال", "لیگ", "باشگاه", "تیم", "بازیکن",
    "سرمربی", "مربی", "گل", "ورزشگاه", "هواداران",
    "دربی", "قهرمانی", "مسابقه", "المپیک", "کشتی",
    "بوکس", "بسکتبال", "والیبال", "دو و میدانی", "مدال",
    "جام جهانی", "فیفا", "کشتی آزاد", "یزدانی", "رضاییان",
]

TOPICS = {
    "فوتبال": "⚽", "والیبال": "🏐", "بسکتبال": "🏀",
    "ورزش": "🏅", "المپیک": "🏟️", "طلایی": "🥇", "نقره": "🥈", "برنز": "🥉",
    "جنگ": "⚔️", "حمله": "💣", "موشک": "🚀", "پدافند": "🛡️",
    "هسته‌ای": "☢️", "شیمیایی": "🧪",
    "زلزله": "🌍", "سیل": "🌊", "طوفان": "🌀",
    "آتش‌سوزی": "🔥", "انفجار": "💥", "بمب": "💣",
    "گروگان": "🔒", "ترور": "🔫",
    "اقتصاد": "💰", "نفت": "🛢️", "گاز": "🔥",
    "بورس": "📈", "تورم": "📉", "دلار": "💵",
    "یورو": "💶", "ارز": "💱", "تحریم": "🚫",
    "انتخابات": "🗳️", "رئیس‌جمهور": "🎩",
    "نخست‌وزیر": "👔", "دولت": "🏛️", "مجلس": "🏛️",
    "قانون": "📜", "مذاکره": "🤝", "توافق": "📝",
    "معاهده": "🕊️", "اعتراض": "✊", "تظاهرات": "🚩",
    "سفر": "✈️", "دیدار": "🤝", "نشست": "👥",
    "فرهنگ": "🎭", "هنر": "🎨", "سینما": "🎬",
    "موسیقی": "🎵", "دانشگاه": "🎓", "مدرسه": "🏫",
    "بیمارستان": "🏥", "کرونا": "😷", "واکسن": "💉",
    "پزشکی": "🩺", "هوش مصنوعی": "🤖", "فضا": "🚀",
    "اینترنت": "🌐", "ماهواره": "🛰️",
    "تصادف": "🚗", "سقوط هواپیما": "✈️",
    "ریزش ساختمان": "🏚️", "غرق": "🚢",
    "آتش‌نشانی": "🚒", "شهید": "🕊️", "شهادت": "🕊️",
}

EXTRA_TOPICS = {
    "پالایشگاه": "🏭🛢️", "پتروشیمی": "🧪🛢️",
    "نفت خام": "🛢️", "گاز طبیعی": "🔥",
    "خط لوله": "🛢️", "انتقال گاز": "🔥",
    "تولید برق": "⚡", "نیروگاه": "⚡🏭", "برق": "⚡",
    "انرژی اتمی": "☢️", "نیروگاه هسته‌ای": "☢️",
    "اورانیوم": "☢️", "غنی‌سازی": "☢️",
    "سوخت فسیلی": "🛢️", "انرژی تجدیدپذیر": "🌞",
    "خورشیدی": "🌞", "بادی": "🌬️", "سد": "💧", "آبگیری": "💧",
    "فرودگاه": "✈️", "پرواز": "✈️", "ایرلاین": "✈️",
    "راه‌آهن": "🚆", "قطار": "🚆", "مترو": "🚇",
    "بزرگراه": "🛣️", "جاده": "🛣️", "پل": "🌉",
    "تونل": "🕳️", "لجستیک": "📦", "حمل‌ونقل": "🚚",
    "کشتیرانی": "🚢", "کانتینر": "📦🚢", "باربری": "🚚", "گمرک": "🏷️",
    "پایگاه": "🏕️", "پادگان": "🎖️", "عملیات": "🎖️",
    "درگیری": "⚔️", "آتش‌بس": "🕊️", "دفاع": "🛡️",
    "مرز": "🚧", "گشت": "🚓", "امنیت": "🔐",
    "اطلاعات": "🕵️", "جاسوسی": "🕵️", "کماندو": "🎖️",
    "حادثه": "🚨", "تصادف": "🚗💥", "ریزش": "🏚️",
    "رانش زمین": "🌍", "آوار": "🧱", "نجات": "🆘",
    "بانک مرکزی": "🏦", "بانک": "🏦", "بهره": "📊",
    "نرخ ارز": "💱", "رکود": "📉", "رشد اقتصادی": "📊",
    "مالیات": "🧾", "بودجه": "💰", "کسری بودجه": "📉",
    "سهام": "📈", "شاخص": "📊",
    "خبر": "📰", "خبرگزاری": "📰", "تلویزیون": "📺",
    "رادیو": "📻", "گزارش": "📄", "پخش زنده": "🔴",
    "مصاحبه": "🎤", "کنفرانس": "🎤", "نشست": "🏛️",
    "بی‌بی‌سی": "📻", "سی‌ان‌ان": "📺", "الجزیره": "📺",
    "بیت کوین": "₿", "اتریوم": "⟠", "تتر": "💵", "بایننس": "🪙",
    "گوگل": "🔍", "مایکروسافت": "💻", "اپل": "🍎",
    "متا": "📱", "تسلا": "⚡",
}

DEFAULT_EMOJI = "✨"

BLOCKED_WORDS = [
    "تبلیغ", "خرید", "فروش", "کسب درآمد", "عضویت", "ارزان", "تخفیف",
    "ویژه", "همین الان", "کلیک کن", "دانلود", "فیلترشکن", "vpn",
    "سرعت عالی", "امنیت بالا", "اتصال پایدار", "فروشی", "مفت", "حراج",
    "ارزون", "ثبت نام", "رایگان", "شرط‌بندی", "شرط بندی", "bet",
    "کازینو", "قمار", "پیش‌بینی ورزشی", "برد تضمینی", "استروئید",
    "فیلم سوپر", "عکس خصوصی", "همسریابی", "دوستیابی",
    "نصب کن", "پیشگوی ما", "جایزه نقدی", "برنده ما باشی",
    "کارت هدیه", "وام فوری", "با امید بانک", "omidbank.ir", "omidbank",
    "برای مشاهده کامل خبر کلیک کنید",
    "متن کامل خبر را اینجا بخوانید",
    "برای اطلاع از جزئیات به لینک زیر مراجعه کنید",
    "بیشتر بخوانید:", "اینجا را کلیک کنید", "جهت کسب اطلاعات بیشتر",
    "برای مطالعه بیشتر به سایت", "جزئیات در:",
    "ادامه‌ی گزارش", "ادامه گزارش",
]

TEXTS_TO_REMOVE = [
    "@iribnews", "t.me/iribnews", "iribnews.ir",
    "@IRNA_1313", "t.me/irna_1313", "irna.ir",
    "@isna94", "t.me/isna94", "isna.ir",
    "@Projectmeshkat", "t.me/Projectmeshkat", "https://zil.ink/ProjectMeshkat",
    "خبرنگار ایرنا", "خبرنگار ایسنا",
    "#گزارش", "#یادداشت", "#اینفو_ایرنا", "#اینفوایرنا", "اینفو ایرنا",
]

PROMO_LINE_PHRASES = [
    "آخرین خبر هرمزگان را در پیام رسان‌های ایرانی دنبال کنید",
    "آخرین خبر را در پیام رسان‌های ایرانی دنبال کنید",
    "ما را در شبکه‌های اجتماعی دنبال کنید",
    "کانال‌های آخرین‌خبر",
    "پیشگوی هوش مصنوعی آخرین خبر",
    "مسابقه پیش‌بینی آخرین خبر",
    "با امید زندگی کن",
    "تحویل بگیر", "ارسال به سراسر ایران", "غیر حضوری", "غیرحضوری",
    "همین الان خرید کنید", "برای خرید کلیک کنید", "تخفیف ویژه", "فروش ویژه",
    "اخبار ایران و جهان را از دریچه ی نگاه",
    "برای اطلاع از آخرین اخبار",
    "جهت اطلاع از اخبار",
    "وب‌سایت:", "تلگرام:", "اینستاگرام:", "واتس‌اپ:",
    "ما را دنبال کنید",
    "مشاهده خبر کامل",
    "🏷 تگ‌ها:",
    "مشروح این #گزارش", "متن کامل این #یادداشت",
    "پخش زنده", "بسته خبری ایرنا", "بسته خبری ایسنا",
    "مرور اخبار روز", "خبرگردی",
]

extra_blocked = os.environ.get("EXTRA_BLOCKED_WORDS", "")
if extra_blocked:
    BLOCKED_WORDS.extend([w.strip() for w in extra_blocked.split(",") if w.strip()])

extra_spam = os.environ.get("EXTRA_SPAM_WORDS", "")
if extra_spam:
    for word in extra_spam.split(","):
        w = word.strip()
        if w:
            PROMO_LINE_PHRASES.append(w)

recent_texts = []
recent_titles = []
MAX_HISTORY = 300

def normalize(text):
    if not text: return ""
    text = text.replace("\u200c", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")
    return re.sub(r"\s+", " ", text).strip()

def count_akharinkhabar(text):
    return len(re.findall(r'آخرین\s?خبر|اخرین\s?خبر', text))

def is_spam_line(line, prev_line=None, next_line=None):
    if re.search(r'https?://(?:rubika\.ir|ble\.ir|eitaa\.com|splus\.ir|gap\.im)', line):
        return True
    if re.search(r'https?://t\.me/akharinkhabar', line):
        return True
    if re.search(r'akharinkhabar\.ir', line):
        return True
    if re.search(r'https?://', line) and re.search(r'(کلیک کنید|همین حالا|بازدید کنید|ثبت نام|همین الان|برای اطلاعات بیشتر|جهت مشاهده|اطلاعات بیشتر|اینجا کلیک کنید|برای خرید|تخفیف ویژه|همین الان عضو شوید|همین الان دانلود کنید)', line, re.IGNORECASE):
        return True
    if re.search(r'(کارت\s?هدیه|غیر\s?حضوری|تحویل بگیر|با امید بانک|طرح ویژه|اعتبار|سپرده|سود علی‌الحساب)', line) and re.search(r'https?://', line):
        return True
    if re.fullmatch(r'\s*(وب‌سایت|تلگرام|اینستاگرام|واتس‌اپ)\s*:?\s*', line):
        return True
    if any(phrase in line for phrase in PROMO_LINE_PHRASES):
        return True
    if next_line is not None:
        if re.search(r'(وب‌سایت|تلگرام|اینستاگرام)\s*:', line) and (not next_line.strip() or re.search(r'https?://', next_line)):
            return True
    if re.search(r'اخبار', line) and re.search(r'(ببینید|دنبال کنید)', line):
        if prev_line and re.search(r'(وب‌سایت|تلگرام|اینستاگرام)\s*:', prev_line):
            return True
        if next_line and re.search(r'(وب‌سایت|تلگرام|اینستاگرام)\s*:', next_line):
            return True
        if prev_line and re.search(r'https?://', prev_line):
            return True
        if next_line and re.search(r'https?://', next_line):
            return True
        return False
    return False

def remove_promotional_lines(text):
    lines = text.split('\n')
    kept = []
    for i, line in enumerate(lines):
        prev_line = lines[i-1] if i-1 >= 0 else None
        next_line = lines[i+1] if i+1 < len(lines) else None
        if not is_spam_line(line, prev_line, next_line):
            kept.append(line)
    return '\n'.join(kept)

def remove_source_attribution(text):
    lines = text.split('\n')
    kept = []
    for line in lines:
        stripped = line.strip()
        if re.fullmatch(r'(ایرنا|ایسنا|#ایرنا|#ایسنا|#اینفو_ایرنا|اینفو ایرنا|#اینفوایرنا)\s*', stripped):
            continue
        if re.fullmatch(r'^[\s\-🔹]*?(ایرنا|ایسنا)\s*$', stripped):
            continue
        if re.fullmatch(r'#\w+\s*ایرنا\s*', stripped):
            continue
        kept.append(line)
    return '\n'.join(kept)

def clean_text(text):
    if not text: return ""
    text = remove_promotional_lines(text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\S*\.ir\S*", "", text)
    for item in TEXTS_TO_REMOVE:
        text = text.replace(item, "")
    text = remove_source_attribution(text)
    text = re.sub(r"@[^\s]+", "", text)
    text = re.sub(r"\|\s*", "", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()

def is_rubbish(text):
    return not text or len(text.strip()) < 6

def contains_blocked(text):
    return any(bad in normalize(text).lower() for bad in BLOCKED_WORDS)

def has_financial_scam(text):
    if re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', text):
        return True
    if re.search(r'\bIR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', text, re.IGNORECASE):
        return True
    if re.search(r'(pay|zarinpal|idpay|payment|شارژ|کیف پول)', text, re.IGNORECASE):
        return True
    return False

def is_similar(new_text):
    lines = new_text.split('\n', 1)
    title = lines[0].strip()
    title_hash = hashlib.md5(title.encode()).hexdigest()
    if title_hash in recent_titles:
        return True
    for old_text in recent_texts:
        if difflib.SequenceMatcher(None, new_text, old_text).ratio() >= 0.8:
            return True
    recent_titles.append(title_hash)
    if len(recent_titles) > MAX_HISTORY:
        recent_titles.pop(0)
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
    for token in tokens:
        if token in PERSONS:
            return PERSONS[token]
    for token in tokens:
        if token in PLACES:
            return PLACES[token]
    for token in tokens:
        if token in MILITARY:
            return MILITARY[token]
    for token in tokens:
        if token in TOPICS:
            return TOPICS[token]
    for token in tokens:
        if token in EXTRA_TOPICS:
            emojis = list(EXTRA_TOPICS[token])
            if emojis:
                return emojis[0]
    return DEFAULT_EMOJI

def format_news(cleaned_text):
    lines = cleaned_text.split('\n', 1)
    if not lines: return cleaned_text
    title = re.sub(r'#\S+', '', lines[0].strip()).strip()
    title = f"**{title}**"
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

        if contains_blocked(text) or has_financial_scam(text):
            print("⛔ تبلیغ / کلاهبرداری")
            return

        if count_akharinkhabar(text) > 2:
            print("⛔ اسپم برند (تکرار بیش از حد)")
            return

        cleaned = clean_text(text)
        if is_rubbish(cleaned):
            print("⛔ بی‌ارزش")
            return

        if is_similar(cleaned):
            print("⛔ تکراری")
            return

        add_to_history(cleaned)

        header = generate_header(cleaned)
        formatted_body = format_news(cleaned)
        final_text = f"{header}{formatted_body}{MY_SIGNATURE}"

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
    global recent_texts, recent_titles
    while True:
        time.sleep(6 * 3600)
        if len(recent_texts) > 300:
            recent_texts = recent_texts[-300:]
            recent_titles = recent_titles[-300:]
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
        print("🚀 ربات کامل و بی‌نقص احسان روشن شد.")
        with client:
            client.loop.run_until_complete(resolve_dest())
            client.run_until_disconnected()
