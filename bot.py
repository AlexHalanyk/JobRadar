import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("CHAT_ID")


def send_notification(job):
    text = f"🚚  New Order\n{job['route']}\nPrice: £{job['price']}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)