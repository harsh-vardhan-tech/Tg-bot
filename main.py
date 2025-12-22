import os
import asyncio
import random
import logging
from datetime import datetime

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from groq import Groq

# -------------------- BASIC LOGGING --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# -------------------- ENV VARIABLES --------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AI_ENABLED = os.getenv("AI_ENABLED", "1")

if not BOT_TOKEN or not OWNER_ID:
    raise RuntimeError("Missing ENV variables")

OWNER_ID = int(OWNER_ID)

# -------------------- AI CLIENT --------------------
groq_client = None
if AI_ENABLED == "1" and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)

# -------------------- BOT MEMORY --------------------
BOT_RULES = (
    "You are Anushri, a sweet, expressive, human-like girl. "
    "Reply naturally in Hinglish. "
    "Do not repeat same lines. "
    "Use emojis sometimes, not always. "
    "Be calm, friendly, slightly playful. "
    "Never say you are an AI or bot."
)

CHAT_HISTORY = {}  # chat_id -> list of messages

EMOJIS = ["😊", "😉", "✨", "😌", "🤍", "😄", "🙈", "💫"]

# -------------------- HELPERS --------------------
def human_delay():
    return random.uniform(1.8, 2.5)

def random_emoji():
    if random.random() < 0.4:
        return " " + random.choice(EMOJIS)
    return ""

async def typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

# -------------------- OWNER COMMANDS --------------------
async def set_rule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_RULES
    if update.effective_user.id != OWNER_ID:
        return

    new_rule = " ".join(context.args)
    if not new_rule:
        await update.message.reply_text("Rule likho 🙂")
        return

    BOT_RULES = new_rule
    await update.message.reply_text("✅ Rule updated")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(
        f"✅ Bot running\n"
        f"AI: {'ON' if groq_client else 'OFF'}\n"
        f"Time: {datetime.now()}"
    )

# -------------------- AI REPLY --------------------
async def ai_reply(chat_id: int, user_text: str) -> str:
    if not groq_client:
        return "Hmm 😊 bolo na"

    history = CHAT_HISTORY.get(chat_id, [])
    history.append({"role": "user", "content": user_text})
    history = history[-6:]

    messages = [{"role": "system", "content": BOT_RULES}] + history

    try:
        resp = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.8,
            max_tokens=120,
        )

        reply = resp.choices[0].message.content.strip()
        history.append({"role": "assistant", "content": reply})
        CHAT_HISTORY[chat_id] = history
        return reply + random_emoji()

    except Exception as e:
        logging.error(e)
        return "Thoda sa ruk jao na 😅"

# -------------------- MESSAGE HANDLER --------------------
async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    await typing(context, chat_id)
    await asyncio.sleep(human_delay())

    reply = await ai_reply(chat_id, text)
    await update.message.reply_text(reply)

# -------------------- START --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hii 😊 Anushri here...\n"
        "bolo kya baat hai ✨"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rule", set_rule))
    app.add_handler(CommandHandler("status", status))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    logging.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
