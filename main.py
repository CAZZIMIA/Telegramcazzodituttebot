
import os
import telebot
from flask import Flask
from openai import OpenAI
from threading import Thread

# CONFIGURAZIONE
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN mancante su Render!")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN mancante su Render!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# HUGGING FACE
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# COMANDO START
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(
        message,
        "🤖 Ciao! Sono Cazzodituttebot!\n\n"
        "Sono online e collegato a DeepSeek. "
        "Scrivimi qualcosa per iniziare!"
    )
    print("Comando /start ricevuto!")

# MESSAGGI AI
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        if not message.text:
            return

        print("Messaggio ricevuto:", message.text)

        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=[
                {"role": "user", "content": message.text}
            ],
            max_tokens=500
        )

        answer = response.choices[0].message.content

        if answer:
            bot.reply_to(message, answer)
        else:
            bot.reply_to(message, "DeepSeek non ha restituito una risposta.")

    except Exception as e:
        print("ERRORE HUGGING FACE:", str(e))
        bot.reply_to(message, "Si è verificato un errore con il servizio AI.")

# FLASK
@app.route('/')
def home():
    return "Cazzodituttebot is running!"

def run_flask():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

# AVVIO
if __name__ == "__main__":
    print("Avvio Telegram bot...")

    me = bot.get_me()
    print(f"Telegram collegato: @{me.username}")

    Thread(target=run_flask, daemon=True).start()

    print("Avvio polling Telegram...")

    bot.infinity_polling(
        skip_pending=True,
        logger_level=20
    )
