from telegram import Bot
from config import NOTIFY_BOT_TOKEN, NOTIFY_CHAT_ID

_bot = Bot(token=NOTIFY_BOT_TOKEN)


async def send_notification(text: str):
    try:
        await _bot.send_message(
            chat_id=NOTIFY_CHAT_ID,
            text=text,
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"[Notifier] Gagal kirim notif: {e}")


def format_signal(signal: dict) -> str:
    emoji = "🟢" if signal["direction"] == "LONG" else "🔴"
    lines = [
        f"{emoji} <b>{signal['direction']} {signal['coin']}USDT</b>",
        f"📍 Entry  : <code>{signal['entry']}</code>",
        f"🎯 TP1    : <code>{signal['tp1']}</code>",
    ]
    if signal.get("tp2"):
        lines.append(f"🎯 TP2    : <code>{signal['tp2']}</code>")
    if signal.get("tp3"):
        lines.append(f"🎯 TP3    : <code>{signal['tp3']}</code>")
    lines.append(f"🛑 SL     : <code>{signal['sl']}</code>")
    return "\n".join(lines)


def format_result(result: dict) -> str:
    mode = "⚠️ TESTNET" if result["testnet"] else "✅ LIVE"
    orders_text = ""
    for o in result["orders"]:
        label = o["type"].upper()
        orders_text += f"\n  • {label}: <code>{o.get('price', '?')}</code>"

    return (
        f"{mode} — Order Executed!\n\n"
        f"📊 <b>{result['direction']} {result['symbol']}</b>\n"
        f"⚡ Leverage  : <b>{result['leverage']}x</b>\n"
        f"📦 Qty       : <code>{result['quantity']}</code>\n"
        f"💵 Risk      : <code>{result['risk_usdt']} USDT (1%)</code>\n"
        f"\nOrders:{orders_text}"
    )
