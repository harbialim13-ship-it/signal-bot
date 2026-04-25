import asyncio
import os
import tempfile
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto

from config import (
    TELEGRAM_API_ID, TELEGRAM_API_HASH,
    TELEGRAM_PHONE, TELEGRAM_SESSION_STR, SIGNAL_CHANNEL,
)
from signal_parser import parse_signal_image, parse_signal_text
from binance_trader import open_trade
from notifier import send_notification, format_signal, format_result

# Pakai StringSession jika tersedia (Railway), fallback ke file lokal
_session = StringSession(TELEGRAM_SESSION_STR) if TELEGRAM_SESSION_STR else "signal_session"
client = TelegramClient(_session, TELEGRAM_API_ID, TELEGRAM_API_HASH)


async def handle_new_message(event):
    message = event.message
    text    = message.text or ""
    signal  = None

    print(f"\n[Listener] Pesan baru diterima")

    # ── Gambar (dengan atau tanpa caption) ────────────────────────
    if message.media and isinstance(message.media, MessageMediaPhoto):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            await message.download_media(tmp_path)
            signal = parse_signal_image(tmp_path)

            # Fallback ke caption kalau gambar tidak terparsing
            if not signal.get("valid") and text:
                print("[Listener] Image parse gagal, coba parse caption...")
                signal = parse_signal_text(text)
        finally:
            os.unlink(tmp_path)

    # ── Teks saja ─────────────────────────────────────────────────
    elif text:
        signal = parse_signal_text(text)

    # ── Bukan sinyal ──────────────────────────────────────────────
    if not signal or not signal.get("valid"):
        print("[Listener] Bukan sinyal trading, dilewati.")
        return

    # ── Ada sinyal valid → notify user ───────────────────────────
    await send_notification(
        f"📡 <b>Sinyal terdeteksi!</b>\n\n{format_signal(signal)}\n\n⏳ Eksekusi..."
    )

    # ── Eksekusi order ────────────────────────────────────────────
    try:
        result = open_trade(signal)
        await send_notification(format_result(result))
        print(f"[Listener] Order berhasil: {result['symbol']} {result['direction']}")
    except Exception as e:
        err_msg = f"❌ <b>Order gagal!</b>\n<code>{str(e)}</code>"
        await send_notification(err_msg)
        print(f"[Listener] Error: {e}")


async def start():
    # Di Railway session sudah ada di env var, tidak perlu input HP lagi
    if TELEGRAM_SESSION_STR:
        await client.start()
    else:
        await client.start(phone=TELEGRAM_PHONE)
    print("[Listener] Terhubung ke Telegram!")

    # Cari channel dari daftar dialog (untuk private channel tanpa username)
    channel = None
    target_id = str(SIGNAL_CHANNEL).replace("-100", "").strip()
    async for dialog in client.iter_dialogs():
        dialog_id = str(dialog.entity.id)
        if dialog_id == target_id or str(dialog.entity.id) == SIGNAL_CHANNEL:
            channel = dialog.entity
            print(f"[Listener] Channel ditemukan: {dialog.name}")
            break

    if channel is None:
        raise ValueError(f"Channel tidak ditemukan: {SIGNAL_CHANNEL}. Pastikan akun Telegram kamu sudah join channel tersebut.")

    client.add_event_handler(
        handle_new_message,
        events.NewMessage(chats=channel),
    )
    print(f"[Listener] Memantau channel: {SIGNAL_CHANNEL}")
    print("[Listener] Bot aktif, menunggu sinyal...\n")
    await client.run_until_disconnected()
