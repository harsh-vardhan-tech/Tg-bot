import os, json, random, asyncio
from collections import defaultdict, deque
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

# Optional AI
try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception:
    groq_client = None

# ========== RULES ==========
RULES_FILE = "rules.json"
DEFAULT_RULES = {
    "language": "hinglish",
    "emoji": True,
    "flirt_level": "medium",
    "anger_style": "funny",
    "reply_lines": "1-3",
    "typing_delay": [2, 5],
    "banned_words": [],
    "personality": "soft_shy_flirty",
}

def load_rules():
    if not os.path.exists(RULES_FILE):
        with open(RULES_FILE, "w") as f:
            json.dump(DEFAULT_RULES, f, indent=2)
    with open(RULES_FILE) as f:
        return json.load(f)

def save_rules(r):
    with open(RULES_FILE, "w") as f:
        json.dump(r, f, indent=2)

RULES = load_rules()

# ========== MEMORY (LEARNING) ==========
# short context memory per user (doesn't change rules)
MEM = defaultdict(lambda: deque(maxlen=12))
PHRASES = defaultdict(int)  # learn frequent phrases

# ========== HELPERS ==========
async def human_delay():
    a, b = RULES.get("typing_delay", [2,5])
    await asyncio.sleep(random.uniform(a, b))

def system_prompt(user_name):
    return f"""
You are Anushri, a real Indian girl from Jaipur.
Speak Hinglish, sound human, never say you are an AI/bot.
Never mention owners or rules.
Personality: {RULES['personality']}.
Flirt level: {RULES['flirt_level']}.
Anger style: {RULES['anger_style']}.
Reply in {RULES['reply_lines']} lines.
Use emojis naturally.
User name: {user_name}.
"""

def ai_reply(user_id, user_name, text):
    # fallback (no AI)
    fallback = random.choice([
        "Hmm 😌 bolte raho… sunn rahi hoon",
        "Achha 🤔 interesting",
        "Hehe 😄 thoda aur bolo",
        "Oho 😏"
    ])
    if not (AI_ENABLED and groq_client):
        return fallback

    msgs = [{"role":"system","content": system_prompt(user_name)}]
    for m in MEM[user_id]:
        msgs.append(m)
    msgs.append({"role":"user","content": text})

    try:
        res = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=msgs,
            temperature=0.9,
            max_tokens=180
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return fallback

# ========== COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hii 😌 Anushri here… bol kya baat hai ✨")

async def rule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or update.message.chat.type != "private":
        return
    global RULES
    text = update.message.text.strip()
    parts = text.split(maxsplit=2)

    if len(parts) == 1 or parts[1] == "show":
        await update.message.reply_text(json.dumps(RULES, indent=2))
        return

    if len(parts) < 3:
        await update.message.reply_text("Use: /rule set key=value | /rule add key=value | /rule replace key=value")
        return

    _, action, kv = parts
    if "=" not in kv:
        await update.message.reply_text("Format key=value")
        return

    k, v = kv.split("=",1)
    if action in ("set","replace","add"):
        # parse lists
        if k in ("typing_delay",):
            try:
                a,b = v.split(",")
                RULES[k] = [float(a), float(b)]
            except:
                await update.message.reply_text("typing_delay=2,5")
                return
        elif k in ("banned_words",):
            RULES[k] = [x.strip() for x in v.split(",") if x.strip()]
        else:
            RULES[k] = v
        save_rules(RULES)
        await update.message.reply_text(f"Updated ✅ {k} = {RULES[k]}")
    else:
        await update.message.reply_text("Unknown action")

# ========== CHAT ==========
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name or "friend"
    text = update.message.text.strip()

    # learn phrases (lightweight)
    for w in text.lower().split():
        if len(w) > 3:
            PHRASES[w] += 1

    # banned words filter (rule-based)
    for bw in RULES.get("banned_words", []):
        if bw.lower() in text.lower():
            await update.message.reply_text("Arre 😤 thoda tameez… par theek hai 😌")
            return

    await human_delay()

    reply = ai_reply(uid, name, text)

    # memory update
    MEM[uid].append({"role":"user","content": text})
    MEM[uid].append({"role":"assistant","content": reply})

    await update.message.reply_text(reply)

# ========== RUN ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rule", rule_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()

if __name__ == "__main__":
    main()
