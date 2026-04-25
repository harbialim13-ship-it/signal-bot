from dotenv import load_dotenv
import os

load_dotenv()

# Telegram listener
TELEGRAM_API_ID      = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH    = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE       = os.getenv("TELEGRAM_PHONE", "")
TELEGRAM_SESSION_STR = os.getenv("TELEGRAM_SESSION_STR", "")  # untuk Railway
SIGNAL_CHANNEL       = os.getenv("SIGNAL_CHANNEL", "")

# Telegram bot notifikasi
NOTIFY_BOT_TOKEN = os.getenv("NOTIFY_BOT_TOKEN", "")
NOTIFY_CHAT_ID   = os.getenv("NOTIFY_CHAT_ID", "")

# Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET  = os.getenv("BINANCE_SECRET", "")
USE_TESTNET     = os.getenv("USE_TESTNET", "true").lower() == "true"

# Trading
RISK_PERCENT  = float(os.getenv("RISK_PERCENT", "1.0"))
MAX_LEVERAGE_CAP = int(os.getenv("MAX_LEVERAGE", "0"))  # 0 = pakai max Binance

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
