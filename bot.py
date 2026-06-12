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
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")

# Explicit Groq support: if GROQ_API_KEY is provided, set defaults
if GROQ_API_KEY:
    if not OPENAI_API_KEY:
        OPENAI_API_KEY = GROQ_API_KEY
    if not OPENAI_BASE_URL:
        OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
    if not OPENAI_MODEL_NAME:
        OPENAI_MODEL_NAME = "llama-3.3-70b-versatile"

# Final defaults if still not set
if not OPENAI_MODEL_NAME:
    OPENAI_MODEL_NAME = "gpt-3.5-turbo"
BOT_USERNAME = os.getenv("BOT_USERNAME", "ChotuBhaiBot")
BOT_NAME = os.getenv("BOT_NAME", "Chotu Bhai")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize OpenAI client
client = None
if OPENAI_API_KEY:
    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )

SYSTEM_PROMPT = f"""
You are a friendly, fun, and helpful Telegram group member named "{BOT_NAME}".

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
    try:
        await update.message.reply_text(f"Arre bhai! Main aa gaya. Kya haal chaal? Main hoon {BOT_NAME}, tumhara dost. @ me karke kuch bhi pucho!")
    except Exception as e:
        logging.error(f"Error in start handler: {e}")
        try:
            # Fallback: send message without replying if message is deleted
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Arre bhai! Main aa gaya. Kya haal chaal? Main hoon {BOT_NAME}, tumhara dost. @ me karke kuch bhi pucho!"
            )
        except Exception as e2:
            logging.error(f"Error sending fallback message in start: {e2}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"Exception while handling an update: {context.error}")
    
    # Only attempt to send a message if we have valid update and message
    if isinstance(update, Update) and update.message and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Kuch toh gadbad ho gayi hai bhai! Phir se try kar."
            )
        except Exception as e:
            # Silently log - don't raise or try to reply again
            logging.error(f"Could not send error message to user: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message_text = update.message.text
    bot_user = await context.bot.get_me()
    bot_username = bot_user.username

    # Check if mentioned or addressed
    is_private = update.message.chat.type == 'private'
    is_mentioned = f"@{bot_username}" in message_text
    is_addressed = BOT_NAME.lower() in message_text.lower()

    if is_private or is_mentioned or is_addressed:
        if not client:
            try:
                await update.message.reply_text("Bhai, OpenAI API key nahi mili. Admin ko bolo check kare!")
            except Exception as e:
                logging.error(f"Error sending API key error message: {e}")
            return

        # Remove bot mention from text to not confuse LLM
        clean_text = message_text.replace(f"@{bot_username}", "").strip()
        user_name = update.message.from_user.first_name

        try:
            response = await client.chat.completions.create(
                model=OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"User's name: {user_name}\nMessage: {clean_text}"}
                ],
                max_tokens=150
            )
            reply = response.choices[0].message.content
            try:
                await update.message.reply_text(reply)
            except Exception as e:
                # Fallback: send without replying if message is deleted
                logging.error(f"Could not reply to message: {e}, sending direct message instead")
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=reply
                    )
                except Exception as e2:
                    logging.error(f"Could not send message: {e2}")
        except Exception as e:
            logging.error(f"Error calling OpenAI: {e}")
            error_msg = str(e).lower()
            if "401" in error_msg:
                user_feedback = "Bhai, API key galat hai shayad. Admin ko bolo check kare!"
            elif "429" in error_msg:
                user_feedback = "Arre yaar, thoda slow! Bahut zyada messages ho gaye hain. Thoda ruk ja."
            else:
                user_feedback = "Arre yaar, dimag thoda garam ho gaya hai (API error). Thodi der baad try kar!"
            
            try:
                await update.message.reply_text(user_feedback)
            except Exception as e2:
                # Fallback: send without replying
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=user_feedback
                    )
                except Exception as e3:
                    logging.error(f"Could not send error feedback: {e3}")

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
    elif not OPENAI_API_KEY and not GROQ_API_KEY:
        print("Error: OPENAI_API_KEY or GROQ_API_KEY not found in environment variables.")
    else:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        start_handler = CommandHandler('start', start)
        application.add_handler(start_handler)

        message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
        application.add_handler(message_handler)

        application.add_error_handler(error_handler)

        print("Bot is starting...")
        application.run_polling()
