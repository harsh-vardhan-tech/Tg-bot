import os
import random
import re
import asyncio
from collections import defaultdict
from telegram import Update, ReactionTypeEmoji
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# 🔐 ENV / CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_IDS = set(
    int(x.strip())
    for x in os.getenv("OWNER_IDS", "").split(",")
    if x.strip().isdigit()
)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in environment variables")

# =========================
# 🧠 MEMORY (IN-MEMORY)
# =========================
OWNER_RULES = {}          # trigger -> reply
GROUP_STYLE = defaultdict(lambda: {
    "emoji_density": "heavy",   # light / medium / heavy
})
LAST_EMOJIS = defaultdict(list)

# =========================
# 😀 EMOJI BANKS (SAFE)
# =========================
ROMANCE_EMOJIS = list("🌚🌝🌷🌹💒💍💖💗💞💓😻😽🥰🤭🫣🤗🫂💋👀✨")
FUNNY_EMOJIS   = list("😂🤣😜🤪🙈🙉🙊🐒🐶🐱🐸🔥⭐")
ROAST_EMOJIS   = list("😏🙄😜👀🐵")
SAD_EMOJIS     = list("🥺😔💔🌧️🫂")
NEUTRAL_EMOJIS = list("🙂😌😉😊😅")

ALL_EMOJIS = list(set(
    ROMANCE_EMOJIS + FUNNY_EMOJIS + ROAST_EMOJIS + SAD_EMOJIS + NEUTRAL_EMOJIS
))

# =========================
# 🚫 PATTERN FILTERS (NO REPEAT)
# =========================
ABUSE_PATTERNS = [
    r"\b(mc|bc)\b",      # examples (masked handling)
    r"\bgali\b",
]
EXPLICIT_PATTERNS = [
    r"\bexplicit\b",
]

def looks_abusive(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in ABUSE_PATTERNS + EXPLICIT_PATTERNS)

# =========================
# 🎭 TYPE DETECTION (SOFT)
# =========================
def detect_type(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["love", "miss", "cute", "jaan"]):
        return "romance"
    if any(w in t for w in ["lol", "haha", "😂"]):
        return "funny"
    if any(w in t for w in ["chal", "arey"]):
        return "roast"
    return "normal"

# =========================
# 👑 OWNER COMMAND PARSER
# =========================
def parse_owner_cmd(text: str):
    # formats:
    # add: a=b
    # replace: a=b
    # delete: a
    # seekh: text
    t = text.strip()
    low = t.lower()
    if low.startswith("add:") or low.startswith("replace:"):
        body = t.split(":",1)[1].strip()
        if "=" in body:
            k,v = body.split("=",1)
            return ("set", k.strip().lower(), v.strip())
    if low.startswith("delete:"):
        k = t.split(":",1)[1].strip().lower()
        return ("del", k, None)
    if low.startswith("seekh:"):
        return ("learn", t.split(":",1)[1].strip(), None)
    return None

# =========================
# 😀 REACTION (ALWAYS)
# =========================
async def react(update: Update, emoji: str):
    try:
        await update.effective_message.set_reaction(
            reaction=[ReactionTypeEmoji(emoji)]
        )
    except:
        pass

def pick_emoji(pool):
    return random.choice(pool)

# =========================
# 💬 REPLY GENERATOR
# =========================
def generate_reply(text: str) -> str:
    kind = detect_type(text)

    if kind == "romance":
        return f"{pick_emoji(ROMANCE_EMOJIS)} {pick_emoji(ROMANCE_EMOJIS)}"
    if kind == "funny":
        return f"{pick_emoji(FUNNY_EMOJIS)}"
    if kind == "roast":
        return f"{pick_emoji(ROAST_EMOJIS)}"
    return f"{pick_emoji(NEUTRAL_EMOJIS)}"

# =========================
# 🤖 MAIN HANDLER
# =========================
async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_message.text:
        return

    user_id = update.effective_user.id
    text = update.effective_message.text.strip()

    # 👉 ALWAYS REACT FIRST
    await react(update, pick_emoji(ALL_EMOJIS))

    # 👑 OWNER OVERRIDE
    if user_id in OWNER_IDS:
        cmd = parse_owner_cmd(text)
        if cmd:
            typ, k, v = cmd
            if typ == "set":
                OWNER_RULES[k] = v
                await update.effective_message.reply_text("done 👍")
            elif typ == "del":
                OWNER_RULES.pop(k, None)
                await update.effective_message.reply_text("removed 👍")
            elif typ == "learn":
                await update.effective_message.reply_text("yaad rakh liya 😌")
            return
        # owner normal chat
        await update.effective_message.reply_text(generate_reply(text))
        return

    # 🔒 OWNER RULE MATCH
    key = text.lower()
    if key in OWNER_RULES:
        await update.effective_message.reply_text(OWNER_RULES[key])
        return

    # 🚫 ABUSE / EXPLICIT → DEFLECT (NO REPEAT)
    if looks_abusive(text):
        # reaction already sent; optional soft line
        if random.random() < 0.4:
            await update.effective_message.reply_text("bas 😐")
        return

    # 💬 NORMAL FLOW
    await update.effective_message.reply_text(generate_reply(text))

# =========================
# 🚀 START APP
# =========================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("Bot running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
