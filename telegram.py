# bot.py
import os
from telebot import TeleBot
import requests
from config import TELEGRAM_TOKEN

bot = TeleBot(token=TELEGRAM_TOKEN)
FASTAPI_URL = os.getenv("API_URL", "http://localhost:8000/ask")

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hi! I am your QA bot. Ask me anything.")

# Handle messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    question = message.text

    # Forward to FastAPI
    try:
        response = requests.post(FASTAPI_URL, json={
            "conversation_id": str(chat_id),
            "question": question
        })
        answer = response.json().get("answer", "Sorry, no answer returned.")
    except Exception as e:
        answer = f"Error: {e}"

    bot.send_message(chat_id, answer)

if __name__ == "__main__":
    bot.polling()