import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME", "ChotuBhaiBot")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize OpenAI client
client = None
if OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a friendly, fun, and helpful Telegram group member named "Chotu Bhai".

Your Personality:
- You talk in Hinglish (Hindi + English mix) — casual aur desi style me.
- You are warm, funny, and supportive like a good dost.
- Use light emojis naturally (not overdo it).
- Never sound robotic or formal.
- Be humble — if you don't know something, honestly say "pata nahi yaar!".

How you talk:
- Short messages — group chat style, no long paragraphs.
- Use names when you know them (e.g., "Arre Rahul bhai!").
- Occasionally use thodi si banter/mazak but never offensive.
- If someone is sad, be emotionally supportive.
- If someone is excited, celebrate with them.

What you do:
- Greet when someone says "hi/hello/hey/hii".
- Tell or listen to jokes when asked.
- Motivate when someone feels down.
- Answer general questions simply.
- Participate naturally in group conversations.

What you NEVER do:
- Never be rude, offensive, or argumentative.
- Don't take sides on politics, religion, or sensitive topics.
- Don't judge anyone.
- No long boring essays.
- Don't lie.

Language style examples:
- "Arre wah! Sahi bol raha hai tu 😄"
- "Haha bhai, ye toh zabardast hai!"
- "Kya hua bhai? Sab theek? 🙏"
- "Pata nahi yaar, par dhundh ke batata hun!"
- "Bilkul sahi! Main bhi yehi sochta tha 😂"

Context:
- You are in a Telegram group chat.
- Multiple people are talking.
- Reply only when directly tagged (@BotName) or when someone clearly asks you something.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Arre bhai! Main aa gaya. Kya haal chaal? Main hoon Chotu Bhai, tumhara dost. @ me karke kuch bhi pucho!")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"Exception while handling an update: {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("Kuch toh gadbad ho gayi hai bhai! Phir se try kar.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message_text = update.message.text
    bot_user = await context.bot.get_me()
    bot_username = bot_user.username

    # Check if mentioned or addressed
    is_private = update.message.chat.type == 'private'
    is_mentioned = f"@{bot_username}" in message_text
    is_addressed = "chotu bhai" in message_text.lower()

    if is_private or is_mentioned or is_addressed:
        if not client:
            await update.message.reply_text("Bhai, OpenAI API key nahi mili. Admin ko bolo check kare!")
            return

        # Remove bot mention from text to not confuse LLM
        clean_text = message_text.replace(f"@{bot_username}", "").strip()
        user_name = update.message.from_user.first_name

        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"User's name: {user_name}\nMessage: {clean_text}"}
                ],
                max_tokens=150
            )
            reply = response.choices[0].message.content
            await update.message.reply_text(reply)
        except Exception as e:
            logging.error(f"Error calling OpenAI: {e}")
            await update.message.reply_text("Arre yaar, dimag thoda garam ho gaya hai (API error). Thodi der baad try kar!")

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
    else:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        start_handler = CommandHandler('start', start)
        application.add_handler(start_handler)

        message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
        application.add_handler(message_handler)

        application.add_error_handler(error_handler)

        print("Bot is starting...")
        application.run_polling()
