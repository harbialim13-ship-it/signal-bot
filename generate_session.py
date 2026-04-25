"""
Jalankan script ini SEKALI di Mac kamu untuk generate session string.
Session string ini nanti diisi ke env var TELEGRAM_SESSION_STR di Railway.

Cara pakai:
    python generate_session.py

Copy output-nya, paste ke Railway sebagai TELEGRAM_SESSION_STR.
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE


async def main():
    print("=" * 50)
    print("  Generate Telegram Session String")
    print("=" * 50)
    print("\nKamu akan diminta kode verifikasi Telegram.\n")

    client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start(phone=TELEGRAM_PHONE)

    session_string = client.session.save()

    print("\n" + "=" * 50)
    print("SESSION STRING KAMU (copy semua teks di bawah ini):")
    print("=" * 50)
    print(session_string)
    print("=" * 50)
    print("\nPaste ke Railway sebagai: TELEGRAM_SESSION_STR")
    print("JANGAN share string ini ke siapapun!\n")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
