
import os
import logging
from threading import Thread

import telebot
from flask import Flask
from openai import OpenAI

# ----------------------------------
# CONFIGURAZIONE E LOG
# ----------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN mancante nelle variabili Render")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN mancante nelle variabili Render")

# ----------------------------------
# TELEGRAM
# ----------------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------
# HUGGING FACE / DEEPSEEK
# ----------------------------------

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
    timeout=90.0,
    max_retries=1
)

MODEL = "deepseek-ai/DeepSeek-R1:fastest"

# ----------------------------------
# FLASK PER RENDER
# ----------------------------------

app = Flask(__name__)


@app.route("/")
def home():
    return "Cazzodituttebot is running!", 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False
    )


# ----------------------------------
# COMANDO START
# ----------------------------------

@bot.message_handler(commands=["start"])
def start_command(message):
    logger.info("Comando /start ricevuto")

    bot.reply_to(
        message,
        "🤖 Ciao! Sono Cazzodituttebot!\n\n"
        "Sono collegato a DeepSeek tramite Hugging Face.\n"
        "Scrivimi qualcosa per iniziare!"
    )


# ----------------------------------
# COMANDO HELP
# ----------------------------------

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.reply_to(
        message,
        "🤖 Puoi scrivermi qualsiasi domanda "
        "e proverò a risponderti con DeepSeek."
    )


# ----------------------------------
# RICEZIONE MESSAGGI
# ----------------------------------

@bot.message_handler(
    content_types=["text"],
    func=lambda message: True
)
def handle_message(message):

    if not message.text:
        return

    user_message = message.text.strip()

    if not user_message:
        return

    logger.info(
        "Messaggio ricevuto da Telegram: chat_id=%s",
        message.chat.id
    )

    try:
        bot.send_chat_action(
            message.chat.id,
            "typing"
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sei Cazzodituttebot, "
                        "un assistente AI disponibile e cordiale. "
                        "Rispondi nella lingua utilizzata dall'utente."
                    )
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=500
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "DeepSeek non ha restituito una risposta."

        # Telegram limita la lunghezza dei messaggi
        for i in range(0, len(answer), 4000):
            bot.reply_to(
                message,
                answer[i:i + 4000]
            )

        logger.info("Risposta AI inviata correttamente")

    except Exception as e:

        status_code = getattr(e, "status_code", None)

        logger.error(
            "ERRORE AI: tipo=%s status=%s dettaglio=%s",
            type(e).__name__,
            status_code,
            str(e)[:1500]
        )

        try:
            bot.reply_to(
                message,
                "⚠️ Si è verificato un errore con il servizio AI.\n"
                "Riprova tra poco."
            )
        except Exception:
            logger.exception("Errore durante l'invio del messaggio Telegram")


# ----------------------------------
# MESSAGGI NON TESTUALI
# ----------------------------------

@bot.message_handler(
    content_types=[
        "photo",
        "document",
        "audio",
        "video",
        "voice",
        "sticker"
    ]
)
def handle_non_text(message):
    bot.reply_to(
        message,
        "Per ora posso rispondere ai messaggi di testo."
    )


# ----------------------------------
# AVVIO PROGRAMMA
# ----------------------------------

if __name__ == "__main__":

    logger.info("Avvio Telegram bot...")

    try:
        me = bot.get_me()

        logger.info(
            "Telegram collegato: @%s",
            me.username
        )

        flask_thread = Thread(
            target=run_flask,
            daemon=True
        )
        flask_thread.start()

        logger.info("Avvio polling Telegram...")

        bot.infinity_polling(
            timeout=30,
            long_polling_timeout=30,
            skip_pending=False,
            logger_level=logging.INFO
        )

    except Exception:
        logger.exception("ERRORE FATALE NEL BOT")
        raise
