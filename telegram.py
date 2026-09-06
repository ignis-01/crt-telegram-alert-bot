import time
import requests

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=15)
    r.raise_for_status()

def wait_for_chat_id(token, timeout_seconds=600):
    """Wait for the owner to send /start, then return that private chat ID."""
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    deadline = time.time() + timeout_seconds
    offset = None

    while time.time() < deadline:
        params = {"timeout": 20}
        if offset is not None:
            params["offset"] = offset

        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        updates = r.json().get("result", [])

        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message", {})
            text = msg.get("text", "")
            chat = msg.get("chat", {})
            if text.strip().lower() == "/start" and chat.get("id"):
                chat_id = str(chat["id"])
                send_message(token, chat_id, "✅ Dray CRT bot connected. Alerts are now enabled.")
                return chat_id

        time.sleep(1)

    raise TimeoutError("No /start received within the setup window.")
