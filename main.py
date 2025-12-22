# =========================================================
#  ANUSHRI BOT – HUMAN STYLE (SAFE + ADVANCED)
# =========================================================

import os
import random
import asyncio
import sqlite3
from datetime import datetime
from telegram import Update, ChatAction
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

cur.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

db.commit()

def set_setting(k, v):
    cur.execute("REPLACE INTO settings VALUES (?,?)", (k, v))
    db.commit()

def get_setting(k, default):
    cur.execute("SELECT value FROM settings WHERE key=?", (k,))
    r = cur.fetchone()
    return r[0] if r else default

# default modes
set_setting("flirt", "on")
set_setting("roast", "on")
set_setting("emoji", "max")

# ================= EMOJIS =================
EMOJI_HAPPY = ["😂","🤣","😜","🤪","😎","🌚","🐒","✨","😌"]
EMOJI_FLIRT = ["🥹","😏","😌","❤️","💫","🌹","😻"]
EMOJI_ROAST = ["🤡","🙄","😒","💀","😤"]
EMOJI_SAD   = ["🥲","😔","💔","🫂"]

# ================= LINES =================
FLIRT_LINES = [
    "Aise baat karega toh main thoda smile kar deti hoon 😏",
    "Hmm… attitude notice ho raha hai 😌",
    "Tu zyada bolta nahi, par effect aa jata hai 😜",
]

ROAST_LINES = [
    "Hero mat ban, dialogue kam maar 🤡",
    "Itna confidence? mirror se baat karke aaya hai kya 🙄",
    "Tu alag hi level ka specimen hai 😂",
]

FUNNY_LINES = [
    "Has le bhai, free hai 😂",
    "Dimag load mat le, main hoon na 😌",
    "Tu bole jaa, main judge nahi kar rahi 🤭",
]

NEUTRAL_LINES = [
    "Achha…",
    "Hmm… samjhi",
    "Theek hai",
]

OWNER_LINES = [
    "Haan jaan, bolo 😌❤️",
    "Owner mode detected 😎",
    "Aap ka order pehle",
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
    if any(w in t for w in ["love","cute","sweet"]):
        return "flirt"
    if any(w in t for w in ["abe","pagal","faltu"]):
        return "roast"
    return "normal"

async def human_delay(ctx):
    await ctx.bot.send_chat_action(
        chat_id=ctx._chat_id,
        action=ChatAction.TYPING
    )
    await asyncio.sleep(random.uniform(0.8, 2.5))

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Hii 😌\nMain {BOT_NAME} hoon, {LOCATION} se.\nMood pe reply karti hoon 😜"
    )

async def owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(
            "Owner commands:\n"
            "/mode flirt on/off\n"
            "/mode roast on/off\n"
            "/mode emoji max/low"
        )
        return

    key = context.args[0]
    val = context.args[1] if len(context.args) > 1 else ""
    set_setting(key, val)
    await update.message.reply_text(f"Updated {key} → {val}")

# ================= MAIN CHAT =================
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

    await human_delay(context)

    # OWNER PRIORITY
    if is_owner(uid):
        await update.message.reply_text(
            pick(OWNER_LINES) + " " + pick(EMOJI_FLIRT)
        )
        return

    flirt_on = get_setting("flirt", "on") == "on"
    roast_on = get_setting("roast", "on") == "on"

    if mood == "flirt" and flirt_on:
        base = pick(FLIRT_LINES)
        emoji = pick(EMOJI_FLIRT)
    elif mood == "roast" and roast_on:
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
    app.add_handler(CommandHandler("mode", owner_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Anushri bot running…")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
