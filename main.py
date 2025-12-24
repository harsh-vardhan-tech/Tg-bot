import os
import asyncio
import random
from collections import deque
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from groq import Groq

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OWNER_ID = str(os.getenv("OWNER_ID"))

if not BOT_TOKEN or not GROQ_API_KEY or not OWNER_ID:
    raise RuntimeError("Missing ENV variables")

# ===== AI CLIENT =====
client = Groq(api_key=GROQ_API_KEY)

# ===== MEMORY =====
memory = deque(maxlen=5)

# ===== SYSTEM RULE =====
SYSTEM_RULE = """
You are Anushri — a real human girl chatting on Telegram.

Rules:
- Never repeat replies
- Every reply must depend on user's message
- Human, natural, casual
- Emojis sometimes, not always
- No robotic tone
- No fixed sentences
"""

# ===== AI FUNCTION =====
def get_ai_reply(user_text: str) -> str:
    messages = [{"role": "system", "content": SYSTEM_RULE}]
    for m in memory:
        messages.append(m)
    messages.append({"role": "user", "content": user_text})

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=random.uniform(0.9, 1.15),
        messages=messages
    )

    reply = completion.choices[0].message.content.strip()
    return reply

# ===== HANDLER =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global SYSTEM_RULE

    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()

    # OWNER COMMANDS
    if user_id == OWNER_ID:
        if text.startswith("/rule"):
            SYSTEM_RULE = SYSTEM_RULE + "\n" + text.replace("/rule", "").strip()
            await update.message.reply_text("✅ Rule updated")
            return

        if text == "/reset":
            memory.clear()
            await update.message.reply_text("♻️ Memory reset")
            return

    # typing
    await context.bot.send_chat_action(chat_id, "typing")
    await asyncio.sleep(random.uniform(1.5, 2.5))

    try:
        reply = get_ai_reply(text)
        if not reply:
            raise Exception
    except Exception:
        reply = "Hmm 🤔 thoda aur bolo na…"

    # save memory
    memory.append({"role": "user", "content": text})
    memory.append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)

# ===== MAIN =====
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
