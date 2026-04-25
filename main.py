import asyncio
import sys
from config import (
    TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE,
    SIGNAL_CHANNEL, NOTIFY_BOT_TOKEN, NOTIFY_CHAT_ID,
    BINANCE_API_KEY, BINANCE_SECRET, ANTHROPIC_API_KEY,
    USE_TESTNET,
)


def check_config():
    """Pastikan semua config wajib sudah diisi"""
    missing = []
    checks = {
        "TELEGRAM_API_ID": TELEGRAM_API_ID,
        "TELEGRAM_API_HASH": TELEGRAM_API_HASH,
        "TELEGRAM_PHONE": TELEGRAM_PHONE,
        "SIGNAL_CHANNEL": SIGNAL_CHANNEL,
        "NOTIFY_BOT_TOKEN": NOTIFY_BOT_TOKEN,
        "NOTIFY_CHAT_ID": NOTIFY_CHAT_ID,
        "BINANCE_API_KEY": BINANCE_API_KEY,
        "BINANCE_SECRET": BINANCE_SECRET,
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
    }
    for key, val in checks.items():
        if not val or str(val) == "0":
            missing.append(key)

    if missing:
        print("❌ Config berikut belum diisi di file .env:")
        for m in missing:
            print(f"   - {m}")
        sys.exit(1)


def main():
    print("=" * 50)
    print("  Crypto Signal Bot - Telegram → Binance Futures")
    print("=" * 50)

    check_config()

    mode = "⚠️  TESTNET" if USE_TESTNET else "🔴 LIVE TRADING"
    print(f"\nMode: {mode}")
    print("Semua config OK. Memulai listener...\n")

    from telegram_listener import start
    asyncio.run(start())


if __name__ == "__main__":
    main()
