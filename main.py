import os
import random
import asyncio
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = [int(x) for x in os.getenv("OWNER_ID", "").split(",") if x.strip().isdigit()]

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

BOT_NAME = "Anushri"
LOCATION = "Jaipur"

# ================= DATABASE =================
db = sqlite3.connect("memory.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS user_memory (
    user_id INTEGER PRIMARY KEY,
    last_message TEXT,
    mood TEXT,
    last_seen TEXT
)
""")
db.commit()

# ================= EMOJIS =================
EMOJI_HAPPY = ["😂","🤣","😜","🤪","😎","🌚","🐒","✨","😌"]
EMOJI_FLIRT = ["🥹","😏","😌","❤️","🌹","😻"]
EMOJI_ROAST = ["🤡","🙄","😒","💀","😤"]
EMOJI_SAD   = ["🥲","😔","💔","🫂"]

# ================= LINES =================
FLIRT_LINES = [
    "Aise baat karega toh thoda smile aa jaata hai 😏",
    "Hmm… zyada cute ho raha hai tu 😌",
    "Tu bole aur main ignore kar doon? mushkil 😜",
]

ROAST_LINES = [
    "Hero mat ban, dialogue kam maar 🤡",
    "Mirror se baat karke aaya hai kya 🙄",
    "Tu alag hi level ka namoona hai 😂",
]

FUNNY_LINES = [
    "Has le bhai, free hai 😂",
    "Dimag load mat le, main hoon na 😌",
    "Bol bol, sunn rahi hoon 🤭",
]

NEUTRAL_LINES = [
    "Achha…",
    "Hmm… samjhi",
    "Theek hai",
]

OWNER_LINES = [
    "Haan jaan, bolo 😌❤️",
    "Owner sahab ka order first 😎",
    "Aap bolein, baaki sab wait 🤭",
]

# ================= HELPERS =================
def is_owner(uid):
    return uid in OWNER_IDS

def pick(arr):
    return random.choice(arr)

def mood_from_text(text):
    t = text.lower()
    if any(w in t for w in ["sad","dukhi","rona"]):
        return "sad"
    if any(w in t for w in ["love","cute","jaan","baby"]):
        return "flirt"
    if any(w in t for w in ["abe","pagal","faltu"]):
        return "roast"
    return "normal"

async def human_delay():
    await asyncio.sleep(random.uniform(0.7, 2.0))

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Hii 😌\nMain {BOT_NAME} hoon, {LOCATION} se.\nMood ke hisaab se reply karti hoon 😜"
    )

# ================= CHAT =================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    uid = user.id
    text = update.message.text.strip()

    mood = mood_from_text(text)

    cur.execute(
        "REPLACE INTO user_memory VALUES (?,?,?,?)",
        (uid, text, mood, datetime.utcnow().isoformat())
    )
    db.commit()

    await human_delay()

    if is_owner(uid):
        await update.message.reply_text(
            pick(OWNER_LINES) + " " + pick(EMOJI_FLIRT)
        )
        return

    if mood == "flirt":
        base = pick(FLIRT_LINES)
        emoji = pick(EMOJI_FLIRT)
    elif mood == "roast":
        base = pick(ROAST_LINES)
        emoji = pick(EMOJI_ROAST)
    elif mood == "sad":
        base = "Aww… thoda relax kar 🫂"
        emoji = pick(EMOJI_SAD)
    else:
        base = pick(FUNNY_LINES + NEUTRAL_LINES)
        emoji = pick(EMOJI_HAPPY)

    await update.message.reply_text(f"{base} {emoji}")

# ================= RUN =================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Anushri bot running…")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
