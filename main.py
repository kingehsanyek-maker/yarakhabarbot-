import os
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 31166081
API_HASH = "5a19b28b0417beeb45b23cbf77586257"

# از متغیر Railway استفاده نمی‌کنیم، چون Session جدید می‌سازیم
# فقط برای اینکه Railway متوقف نشود، یک وب‌سرور خالی نمی‌خواهیم
async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("✅ SESSION_STRING جدید شما:")
        print(client.session.save())

import asyncio
asyncio.run(main())
