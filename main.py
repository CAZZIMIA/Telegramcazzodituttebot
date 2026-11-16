import os
import telebot
from flask import Flask
from openai import OpenAI
from threading import Thread

# Configuration
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN mancante!")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN mancante!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Hugging Face Client Setup
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(
        message,
        "🤖 Ciao! Sono Cazzodituttebot!\n\n"
        "Sono online e collegato a DeepSeek. "
        "Scrivimi qualcosa per iniziare!"
    )
    print("Comando /start ricevuto!")
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
    print("Avvio Telegram bot...")

    try:
        me = bot.get_me()
        print(f"Telegram collegato: @{me.username}")

        Thread(target=run_flask, daemon=True).start()

        print("Avvio polling Telegram...")
        bot.infinity_polling(
            skip_pending=True,
            logger_level=20
        )

    except Exception as e:
        print(f"ERRORE AVVIO BOT: {e}")
        raise
