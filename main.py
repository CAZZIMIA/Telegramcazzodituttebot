import os
import telebot
from flask import Flask
from openai import OpenAI
from threading import Thread

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Hugging Face Client Setup
client = OpenAI(
    baseURL="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Prepare the conversation
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1", # Ensure this model is accessible
            messages=[{"role": "user", "content": message.text}],
            max_tokens=500
        )
        
        response = chat_completion.choices[0].message.content
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Flask route to keep the service alive on Render
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    # Start Flask in a separate thread
    Thread(target=run_flask).start()
    # Start Telegram bot
    bot.infinity_polling()
