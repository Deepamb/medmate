import os

import requests


def send_telegram(chat_id: str | None, text: str) -> bool:
    """Send a Telegram message. If not set up, print it instead (useful while developing)."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not chat_id:
        print(f"[notify skipped] to={chat_id}: {text}")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        return r.ok
    except requests.RequestException as exc:
        print(f"[notify failed] {exc}")
        return False