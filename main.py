from telethon import TelegramClient, events
from flask import Flask
from collections import deque
import threading
import hashlib
import re
import os
import logging

# =========================
# تنظیمات
# =========================
API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"

SOURCE_CHANNELS = [
    "KhabarFori",
    "KhabarFooury",
    "akharinkhabar"
]

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

# =========================
# User Client
# =========================
client = TelegramClient("yarakhabar_user", API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    try:
        msg = event.message
        text = msg.message or ""

        cleaned = clean(text)

        if is_rubbish(cleaned):
            return
        if contains_blocked(cleaned):
            return
        if is_duplicate(cleaned):
            return

        add_history(cleaned)

        header = "🚨🌟♦️🚨"
        final_text = f"{header}\n{cleaned}\n{header}{MY_SIGNATURE}"

        if msg.media:
            await client.send_message(DEST_CHANNEL, final_text, file=msg.media)
        else:
            await client.send_message(DEST_CHANNEL, final_text)

        print("✅ ارسال شد")

    except Exception
