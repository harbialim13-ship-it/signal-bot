import anthropic
import base64
import json
import re
import os
from pathlib import Path
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

VISION_PROMPT = """Kamu adalah parser sinyal trading crypto. Analisa gambar chart/sinyal ini.

Ekstrak informasi trading dan kembalikan HANYA JSON valid dengan format berikut:
{
  "valid": true,
  "direction": "LONG" atau "SHORT",
  "coin": "simbol tanpa $ (contoh: HYPER, BTC, ETH, SOL)",
  "entry": angka (harga entry atau titik tengah zona entry),
  "tp1": angka,
  "tp2": angka atau null,
  "tp3": angka atau null,
  "sl": angka
}

Cara baca chart TradingView dalam gambar:
- Zona HIJAU/TEAL di atas = area Take Profit (TP)
- Zona MERAH di bawah = area Stop Loss (SL)
- Area harga saat ini (biru/cyan highlight) atau zona tengah = Entry
- Baca angka-angka di sisi kanan chart dengan teliti

Jika bukan sinyal trading, kembalikan: {"valid": false}
Jangan tambahkan teks lain selain JSON."""

TEXT_PROMPT = """Kamu adalah parser sinyal trading crypto. Ekstrak sinyal dari teks ini.

Kembalikan HANYA JSON valid:
{
  "valid": true,
  "direction": "LONG" atau "SHORT",
  "coin": "simbol (contoh: BTC, ETH, HYPER)",
  "entry": angka,
  "tp1": angka,
  "tp2": angka atau null,
  "tp3": angka atau null,
  "sl": angka
}

Jika bukan sinyal trading, kembalikan: {"valid": false}
Jangan tambahkan teks lain selain JSON.

Teks:
"""

def _extract_json(text: str) -> dict:
    """Ambil JSON dari response Claude"""
    # Coba langsung parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Cari JSON block
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {"valid": False}


def parse_signal_image(image_path: str) -> dict:
    """Parse sinyal trading dari gambar menggunakan Claude Vision"""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    suffix = Path(image_path).suffix.lower()
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png", ".webp": "image/webp"}
    media_type = media_map.get(suffix, "image/jpeg")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": VISION_PROMPT},
                ],
            }
        ],
    )

    result = _extract_json(message.content[0].text)
    if result.get("valid"):
        print(f"[Parser] Signal dari gambar: {result}")
    return result


def parse_signal_text(text: str) -> dict:
    """Parse sinyal trading dari teks"""
    # Skip pesan pendek yang jelas bukan sinyal
    if len(text.strip()) < 10:
        return {"valid": False}

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": TEXT_PROMPT + text,
            }
        ],
    )

    result = _extract_json(message.content[0].text)
    if result.get("valid"):
        print(f"[Parser] Signal dari teks: {result}")
    return result
