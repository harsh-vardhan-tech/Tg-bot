import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ---------- CONFIG ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

OWNER_IDS = {int(x) for x in OWNER_ID.split(",") if x.isdigit()}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Heyyy… Anushri here 😌💖\nSlow replies, fast emotions 😉"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.lower()

    if user.id in OWNER_IDS:
        await update.message.reply_text("🥺 Owner ho aap… jo bolo maan lungi 💕")
        return

    if any(x in text for x in ["hi", "hello", "hey"]):
        await update.message.reply_text("Awww hi 😌✨ itni pyaari entry?")
    elif "love" in text:
        await update.message.reply_text("Love? 😳 dheere bolo… sharm aa rahi hai 💖")
    elif any(x in text for x in ["bc", "mc", "chutiya"]):
        await update.message.reply_text("Arreyy 😤 tameez… par thoda cute tha 🤣")
    else:
        await update.message.reply_text("Hmm 😌 bolte raho… sunn rahi hoon 💭")

# ---------- MAIN ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # ⚠️ THIS IS IMPORTANT
    app.run_polling()   # ❌ no asyncio.run, no loop.close

if __name__ == "__main__":
    main()
