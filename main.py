import os, time, asyncio, re, difflib, threading
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from flask import Flask

# ===== تنظیمات =====
API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"
SESSION_STRING = os.environ.get("SESSION_STRING", "")
SOURCE_CHANNELS = ["KhabarFori", "KhabarFooury", "akharinkhabar", "Projectmeshkat"]
DEST_CHANNEL = "@yarakhabar"
MY_SIGNATURE = "\n@YARAKHABAR📢\n🔷🔹🎯هر لحظه یک خبر تازه🎯🔹🔷"

# ===== لیست‌های واژگان (کامل) =====
PERSONS = {
    "پزشکیان": "🇮🇷", "مسعود پزشکیان": "🇮🇷", "عراقچی": "🇮🇷",
    "سید عباس عراقچی": "🇮🇷", "ظریف": "🇮🇷", "محمدجواد ظریف": "🇮🇷",
    "قالیباف": "🇮🇷", "محمدباقر قالیباف": "🇮🇷", "خامنه‌ای": "🇮🇷",
    "علی خامنه‌ای": "🇮🇷", "رئیسی": "🇮🇷", "ابراهیم رئیسی": "🇮🇷",
    "احمدی‌نژاد": "🇮🇷", "محمود احمدی‌نژاد": "🇮🇷",
    "روحانی": "🇮🇷", "حسن روحانی": "🇮🇷", "خاتمی": "🇮🇷",
    "سید محمد خاتمی": "🇮🇷", "لاریجانی": "🇮🇷", "علی لاریجانی": "🇮🇷",
    "آملی لاریجانی": "🇮🇷", "صادق آملی لاریجانی": "🇮🇷",
    "محسن رضایی": "🇮🇷", "سعید جلیلی": "🇮🇷", "علی‌اکبر ولایتی": "🇮🇷",
    "مصطفی پورمحمدی": "🇮🇷", "اسحاق جهانگیری": "🇮🇷",
    "عبدالناصر همتی": "🇮🇷", "محمدباقر نوبخت": "🇮🇷",
    "محمد نهاوندیان": "🇮🇷", "سید حسن خمینی": "🇮🇷",
    "اسماعیل بقائی": "🇮🇷", "حسین امیرعبداللهیان": "🇮🇷",
    "علی شمخانی": "🇮🇷", "محمد مخبر": "🇮🇷", "عزت‌الله ضرغامی": "🇮🇷",
    "غلامعلی حدادعادل": "🇮🇷", "غلامحسین محسنی اژه‌ای": "🇮🇷",
    "اکبر هاشمی رفسنجانی": "🇮🇷", "محسن هاشمی": "🇮🇷",
    "محمدرضا عارف": "🇮🇷", "علی مطهری": "🇮🇷", "احمد توکلی": "🇮🇷",
    "مصطفی معین": "🇮🇷", "علی‌اکبر ناطق نوری": "🇮🇷",
    "کمال خرازی": "🇮🇷", "محسن مهرعلیزاده": "🇮🇷",
    "محمدرضا باهنر": "🇮🇷", "علیرضا زاکانی": "🇮🇷",
    "پرویز فتاح": "🇮🇷", "محمدرضا تاجیک": "🇮🇷", "علی ربیعی": "🇮🇷",
    "محمدرضا ظفرقندی": "🇮🇷", "بیژن نامدار زنگنه": "🇮🇷",
    "محمد اسلامی": "🇮🇷", "عباس آخوندی": "🇮🇷",
    "محمدجواد آذری جهرمی": "🇮🇷", "احمد وحیدی": "🇮🇷",
    "اسکندر مؤمنی": "🇮🇷", "علی عبدالعلی‌زاده": "🇮🇷",
    "ترامپ": "🇺🇸", "بایدن": "🇺🇸", "پنس": "🇺🇸", "هریس": "🇺🇸",
    "بوش": "🇺🇸", "اوباما": "🇺🇸", "کلینتون": "🇺🇸",
    "مایک پمپئو": "🇺🇸", "جان کری": "🇺🇸", "بلینکن": "🇺🇸",
    "نتانیاهو": "🐀", "صهیونیست": "🐀", "موساد": "🐀",
}

PLACES = {
    "تهران": "🇮🇷", "اصفهان": "🇮🇷", "تبریز": "🇮🇷", "مشهد": "🇮🇷",
    "بندرعباس": "🇮🇷", "خارک": "🇮🇷", "چابهار": "🇮🇷", "بوشهر": "🇮🇷",
    "عسلویه": "🇮🇷", "اهواز": "🇮🇷", "خوزستان": "🇮🇷", "کیش": "🇮🇷",
    "قشم": "🇮🇷", "تنگه هرمز": "🇮🇷", "ابوموسی": "🇮🇷",
    "تنب بزرگ": "🇮🇷", "تنب کوچک": "🇮🇷",
    "بیروت": "🇱🇧", "ضاحیه": "🇱🇧", "صور": "🇱🇧", "صیدا": "🇱🇧",
    "بقاع": "🇱🇧", "نبطیه": "🇱🇧", "بعلبک": "🇱🇧",
    "دمشق": "🇸🇾", "حلب": "🇸🇾", "حمص": "🇸🇾", "لاذقیه": "🇸🇾",
    "طرطوس": "🇸🇾", "ادلب": "🇸🇾", "دیرالزور": "🇸🇾", "قنیطره": "🇸🇾",
    "غزه": "🇵🇸", "رفح": "🇵🇸", "خان یونس": "🇵🇸",
    "جبالیا": "🇵🇸", "بیت لاهیا": "🇵🇸", "نوار غزه": "🇵🇸",
    "جنین": "🇵🇸", "طولکرم": "🇵🇸", "نابلس": "🇵🇸",
    "رام‌الله": "🇵🇸", "الخلیل": "🇵🇸", "بیت لحم": "🇵🇸",
    "اریحا": "🇵🇸", "کرانه باختری": "🇵🇸", "مسجدالاقصی": "🇵🇸",
    "الاقصی": "🇵🇸", "بیت حانون": "🇵🇸", "دیرالبلح": "🇵🇸",
    "بیت جالا": "🇵🇸", "بیت ساحور": "🇵🇸", "قلقیلیه": "🇵🇸",
    "تل‌آویو": "🇮🇱", "قدس": "🇮🇱", "حیفا": "🇮🇱",
    "اشدود": "🇮🇱", "بئرالسبع": "🇮🇱", "الجلیل": "🇮🇱",
    "طبریه": "🇮🇱", "ایلات": "🇮🇱", "عسقلان": "🇮🇱",
    "اشکلون": "🇮🇱", "نتانیا": "🇮🇱", "عکا": "🇮🇱",
    "صفد": "🇮🇱", "نهاریا": "🇮🇱", "هرتزلیا": "🇮🇱",
    "بات یام": "🇮🇱", "حولون": "🇮🇱", "ریشون لتسیون": "🇮🇱",
    "بنی براک": "🇮🇱", "رمات گان": "🇮🇱", "کریات شمونه": "🇮🇱",
    "مرز لبنان": "🇮🇱", "جولان": "🇮🇱", "بلندی‌های جولان": "🇮🇱",
    "صحرای نقب": "🇮🇱", "نقب": "🇮🇱",
    "صنعا": "🇾🇪", "الحدیده": "🇾🇪", "صعده": "🇾🇪", "عدن": "🇾🇪",
    "مأرب": "🇾🇪", "باب المندب": "🇾🇪", "تعز": "🇾🇪",
    "المخا": "🇾🇪", "حجه": "🇾🇪", "الجوف": "🇾🇪",
    "شبوه": "🇾🇪", "حضرموت": "🇾🇪", "المهره": "🇾🇪",
    "ابین": "🇾🇪", "ذمار": "🇾🇪", "البیضاء": "🇾🇪",
    "بغداد": "🇮🇶", "بصره": "🇮🇶", "اربیل": "🇮🇶",
    "موصل": "🇮🇶", "کرکوک": "🇮🇶", "نجف": "🇮🇶",
    "کربلا": "🇮🇶", "الانبار": "🇮🇶", "الرمادی": "🇮🇶",
    "سلیمانیه": "🇮🇶", "دهوک": "🇮🇶", "الحشد الشعبی": "🇮🇶",
    "القائم": "🇮🇶", "زاخو": "🇮🇶", "تلعفر": "🇮🇶", "سامرا": "🇮🇶",
    "ریاض": "🇸🇦", "جده": "🇸🇦", "ینبع": "🇸🇦", "ظهران": "🇸🇦",
    "دمام": "🇸🇦", "نجران": "🇸🇦", "الجبیل": "🇸🇦",
    "خمیس مشیط": "🇸🇦", "تبوک": "🇸🇦", "جازان": "🇸🇦",
    "مکه": "🇸🇦", "مدینه": "🇸🇦", "القصیم": "🇸٬",
    "حائل": "🇸🇦", "الاحساء": "🇸🇦", "راس تنوره": "🇸🇦",
    "بقیق": "🇸🇦", "ابقیق": "🇸🇦", "عرعر": "🇸🇦",
    "الخرج": "🇸🇦", "الطائف": "🇸🇦",
    "دبی": "🇦🇪", "ابوظبی": "🇦🇪", "فجیره": "🇦🇪",
    "شارجه": "🇦🇪", "رأس الخیمه": "🇦🇪", "خورفکان": "🇦🇪",
    "العین": "🇦🇪", "ام القوین": "🇦🇪", "عجمان": "🇦🇪",
    "جبل علی": "🇦🇪", "مصفح": "🇦🇪", "الرویس": "🇦٬",
    "داس": "🇦🇪", "حبشان": "🇦🇪", "الظفره": "🇦🇪",
    "دوحه": "🇶🇦", "العدید": "🇶🇦", "راس لفان": "🇶🇦",
    "الخور": "🇶🇦", "لوسیل": "🇶🇦", "مسیعید": "🇶🇦", "حمد": "🇶🇦",
    "کویت": "🇰🇼", "الاحمدی": "🇰٬", "المطلاع": "🇰🇼",
    "الجهراء": "🇰🇼", "الفحیحیل": "🇰🇼", "الشعیبه": "🇰🇼", "صبحان": "🇰🇼",
    "منامه": "🇧🇭", "المحرق": "🇧🇭", "ستره": "🇧🇭", "الرفاع": "🇧🇭",
    "مسقط": "🇴🇲", "صلاله": "🇴🇲", "دقم": "🇴🇲", "صحار": "🇴🇲",
    "خصب": "🇴🇲", "مسندم": "🇴٬", "نزوی": "🇴🇲", "برکاء": "🇴🇲",
    "صور عمان": "🇴🇲", "عبری": "🇴🇲",
    "آنکارا": "🇹🇷", "استانبول": "🇹🇷", "وان": "🇹🇷",
    "دیاربکر": "🇹🇷", "اینجرلیک": "🇹🇷",
    "مسکو": "🇷🇺", "سن پترزبورگ": "🇷🇺", "سواستوپل": "🇷🇺",
    "کراسنودار": "🇷🇺", "روستوف": "🇷🇺", "بلگورود": "🇷٬",
    "کورسک": "🇷🇺", "بریانسک": "🇷🇺", "کالینینگراد": "🇷🇺",
    "مورمانسک": "🇷🇺", "ولادی‌وستوک": "🇷🇺",
    "نووراسییسک": "🇷🇺", "کازان": "🇷🇺", "تاتارستان": "🇷🇺",
    "سوچی": "🇷🇺", "چچن": "🇷🇺", "گروزنی": "🇷🇺",
    "داغستان": "🇷🇺", "کریمه": "🇷🇺",
    "کی‌یف": "🇺🇦", "اودسا": "🇺🇦",
    "واشنگتن": "🇺🇸", "نیویورک": "🇺٬", "پنتاگون": "🇺🇸",
    "کاخ سفید": "🇺🇸", "فلوریدا": "🇺🇸", "سن دیگو": "🇺🇸",
    "پکن": "🇨🇳", "شانگهای": "🇨🇳", "تایوان": "🇹🇼", "تایپه": "🇹🇼",
    "پیونگ یانگ": "🇰🇵", "سئول": "🇰🇷",
    "لندن": "🇬🇧", "پاریس": "🇫🇷", "برلین": "🇩🇪", "بروکسل": "🇧🇪",
    "کانال سوئز": "🇪🇬", "قاهره": "🇪🇬", "اسکندریه": "🇪🇬",
    "سوئز": "🇪🇬", "پورت سعید": "🇪🇬", "العریش": "🇪🇬",
    "شرم الشیخ": "🇪🇬", "اسماعیلیه": "🇪🇬", "دمیاط": "🇪🇬",
    "المنصوره": "🇪🇬", "طنطا": "🇪🇬", "السوئز": "🇪🇬",
    "شبه جزیره سینا": "🇪🇬", "سینا": "🇪🇬", "رفح مصر": "🇪🇬",
    "جبل الطارق": "🇬🇮",
    "دریای سرخ": "🌊", "خلیج فارس": "🌊", "دریای عمان": "🌊",
    "اقیانوس هند": "🌊", "دریای مدیترانه": "🌊", "خلیج عدن": "🌊",
    "تنگه باب المندب": "🌊", "خلیج عقبه": "🌊",
    "خلیج عمان": "🌊", "آب‌های بین‌المللی": "🌊",
}

MILITARY = {
    "کشتی": "🚢", "ناو": "🚢", "ناوشکن": "🚢",
    "زیردریایی": "🚢", "شناور": "🚢", "هواپیما": "✈️",
    "جنگنده": "✈️", "فانتوم": "✈️", "اف-35": "✈️",
    "سوخو": "✈️", "میگ": "✈️", "رافال": "✈️", "پهپاد": "✈️",
    "موشک": "🚀", "پدافند": "🛡️", "رادار": "📡",
    "رزمایش": "🎖️", "ارتش": "🎖️", "سپاه": "🎖️",
    "نیروی دریایی": "🚢", "نیروی هوایی": "✈️",
}

SPORTS_CONTEXT = [
    "فوتبال", "لیگ", "باشگاه", "تیم", "بازیکن",
    "سرمربی", "مربی", "گل", "ورزشگاه", "هواداران",
    "دربی", "قهرمانی", "مسابقه", "المپیک", "کشتی",
    "بوکس", "بسکتبال", "والیبال", "دو و میدانی", "مدال"
]

TOPICS = {
    "فوتبال": "⚽", "والیبال": "🏐", "کشتی": "🤼",
    "بسکتبال": "🏀", "ورزش": "🏅", "المپیک": "🏟️",
    "طلایی": "🥇", "نقره": "🥈", "برنز": "🥉",
    "جنگ": "⚔️", "حمله": "💣", "موشک": "🚀",
    "پدافند": "🛡️", "هسته‌ای": "☢️", "شیمیایی": "🧪",
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
    "رانش زمین": "🌍", "آوار": "🧱", "آتش‌نشانی": "🚒",
    "نجات": "🆘", "مفقود": "❓", "فوت": "⚰️", "مجروح": "🏥",
    "اپیدمی": "🦠", "ویروس": "🦠", "بیماری": "🧬", "قرنطینه": "🚫",
    "بانک مرکزی": "🏦", "بانک": "🏦", "بهره": "📊",
    "نرخ ارز": "💱", "رکود": "📉", "رشد اقتصادی": "📊",
    "مالیات": "🧾", "بودجه": "💰", "کسری بودجه": "📉",
    "سرمایه": "💰", "سرمایه‌گذاری": "📊", "سهام": "📈", "شاخص": "📊",
    "خبر": "📰", "خبرگزاری": "📰", "تلویزیون": "📺",
    "رادیو": "📻", "گزارش": "📄", "پخش زنده": "🔴",
    "مصاحبه": "🎤", "کنفرانس": "🎤", "نشست": "🏛️",
    "بی‌بی‌سی": "📻", "سی‌ان‌ان": "📺", "الجزیره": "📺",
    "بیت کوین": "₿", "اتریوم": "⟠", "تتر": "💵", "بایننس": "🪙",
    "گوگل": "🔍", "مایکروسافت": "💻", "اپل": "🍎",
    "متا": "📱", "تسلا": "⚡",
}

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
    "| akharinkhabar.ir",
    "t.me/akharinkhabar", "https://t.me/akharinkhabar",
    "@KhabarFori", "@khabarfori", "@KHABARFORI",
    "t.me/KhabarFori", "https://t.me/KhabarFori",
    "@KhabarFooury", "t.me/KhabarFooury",
    "@Projectmeshkat", "t.me/Projectmeshkat",
    "https://zil.ink/ProjectMeshkat",
]

PROMO_LINE_PHRASES = [
    "آخرین خبر هرمزگان را در پیام رسان‌های ایرانی دنبال کنید",
    "آخرین خبر را در پیام رسان‌های ایرانی دنبال کنید",
    "ما را در شبکه‌های اجتماعی دنبال کنید",
    "کانال‌های آخرین‌خبر",
    "پیشگوی هوش مصنوعی آخرین خبر",
    "مسابقه پیش‌بینی آخرین خبر",
]

recent_texts = []
MAX_HISTORY = 200

def normalize(text):
    if not text: return ""
    text = text.replace("\u200c", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")
    return re.sub(r"\s+", " ", text).strip()

def count_akharinkhabar(text):
    """شمارش تعداد ارجاع به برند آخرین خبر"""
    pattern = r'آخرین\s?خبر|اخرین\s?خبر'
    return len(re.findall(pattern, text))

def is_spam_line(line):
    if re.search(r'https?://(?:rubika\.ir|ble\.ir|eitaa\.com|splus\.ir|gap\.im)', line, re.IGNORECASE):
        return True
    if re.search(r'https?://t\.me/akharinkhabar', line, re.IGNORECASE):
        return True
    if re.search(r'akharinkhabar\.ir', line, re.IGNORECASE):
        return True
    if re.search(r'https?://', line) and re.search(r'(کلیک کنید|همین حالا|بازدید کنید|ثبت نام|همین الان|برای اطلاعات بیشتر|جهت مشاهده|اطلاعات بیشتر|اینجا کلیک کنید|برای خرید|تخفیف ویژه|همین الان عضو شوید|همین الان دانلود کنید)', line, re.IGNORECASE):
        return True
    if re.search(r'(کارت هدیه|تسهیلات|وام|سود علی‌الحساب|سپرده|اعتبار|طرح ویژه|غیرحضوری|ارسال به سراسر)', line) and re.search(r'https?://', line):
        return True
    if any(phrase in line for phrase in PROMO_LINE_PHRASES):
        return True
    return False

def remove_promotional_lines(text):
    lines = text.split('\n')
    kept = []
    for line in lines:
        if not is_spam_line(line):
            kept.append(line)
    return '\n'.join(kept)

def clean_text(text):
    if not text: return ""
    text = remove_promotional_lines(text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\S*\.ir\S*", "", text)
    for item in TEXTS_TO_REMOVE:
        text = text.replace(item, "")
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
        if token in TOPICS:
            emoji = TOPICS[token]
            if emoji not in topics:
                topics.append(emoji)
        if token in EXTRA_TOPICS:
            for e in list(EXTRA_TOPICS[token]):
                if e not in topics:
                    topics.append(e)

    final = []
    if countries:
        final.append(countries[0])
    if topics:
        final.append(topics[0])
    if len(countries) > 1 and len(final) < 2:
        final.append(countries[1])
    elif len(topics) > 1 and len(final) < 2:
        final.append(topics[1])

    while len(final) < 2:
        for d in DEFAULT_EMOJIS:
            if d not in final:
                final.append(d)
                break

    return f"{final[0]}{final[1]}"

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
        final_text = f"{header} {formatted_body}{MY_SIGNATURE}"

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
    global recent_texts
    while True:
        time.sleep(6 * 3600)
        if len(recent_texts) > 200:
            recent_texts = recent_texts[-200:]
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
        print("🚀 ربات مینیمال و فوق‌حرفه‌ای احسان روشن شد.")
        with client:
            client.loop.run_until_complete(resolve_dest())
            client.run_until_disconnected()
