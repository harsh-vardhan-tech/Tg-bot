
import os, asyncio, random, logging
from collections import deque
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
AI_API_KEY = os.getenv("AI_API_KEY")

if not BOT_TOKEN or not AI_API_KEY:
    raise RuntimeError("Missing ENV variables")

client = OpenAI(api_key=AI_API_KEY)
logging.basicConfig(level=logging.INFO)

# ================= MEMORY =================
MEMORY = {}        # chat_id -> recent msgs
RULES = []         # owner-defined runtime rules

def get_memory(cid, maxlen=8):
    if cid not in MEMORY:
        MEMORY[cid] = deque(maxlen=maxlen)
    return MEMORY[cid]

# ================= STYLE =================
REACTIONS = ["👍","❤️","😂","🔥","😅","🤔"]
EMOJIS = ["🙂","😊","😉","😏","😌","🤍","✨"]

async def typing(ctx, cid):
    await ctx.bot.send_chat_action(cid, ChatAction.TYPING)
    await asyncio.sleep(2)

async def react(ctx, cid, mid):
    try:
        await ctx.bot.set_message_reaction(cid, mid, random.choice(REACTIONS))
    except:
        pass

# ================= AI =================
def ai(system, history, user):
    msgs = [{"role":"system","content":system}]
    for h in history:
        msgs.append({"role":"user","content":h})
    msgs.append({"role":"user","content":user})

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=msgs,
        temperature=0.7,
    )
    return res.choices[0].message.content.strip()

# ================= SYSTEM PROMPTS =================
def owner_prompt():
    rule_text = "\n".join(f"- {r}" for r in RULES[-15:]) or "- none"
    return f"""
You are a human-like Indian girl.
Owner has highest priority.
Follow owner rules silently.
Never say you are AI or bot.
Rules:
{rule_text}
"""

def user_prompt():
    return """
You are a human-like Indian girl.
Natural Hinglish, short replies.
Emoji sometimes, not always.
No sexual or unsafe content.
Never say you are AI.
"""

# ================= HANDLER =================
async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    cid = msg.chat_id
    uid = msg.from_user.id
    text = msg.text.strip()

    mem = get_memory(cid)
    mem.append(text)

    await react(ctx, cid, msg.message_id)
    await typing(ctx, cid)

    # OWNER COMMANDS (DM ONLY)
    if uid == OWNER_ID and msg.chat.type == "private":
        if text.lower().startswith("rule:"):
            RULES.append(text[5:].strip())
            reply = "Done 😌 rule apply ho gaya ✨"
        elif text.lower().startswith("rules"):
            reply = "Current rules:\n" + "\n".join(RULES) if RULES else "No rules yet 🙂"
        else:
            reply = ai(owner_prompt(), list(mem), text)
    else:
        reply = ai(user_prompt(), list(mem), text)

    reply += " " + random.choice(EMOJIS)

    sent = await msg.reply_text(reply, reply_to_message_id=msg.message_id)
    await react(ctx, cid, sent.message_id)

# ================= START =================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
