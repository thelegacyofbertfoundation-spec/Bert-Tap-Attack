import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURATION ---
# Replace with your actual GitHub Pages URL (Must end in /)
GITHUB_URL = "https://github.com/thelegacyofbertfoundation-spec/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the launcher button to the user."""
    user = update.effective_user
    
    # Launcher button for the Mini App
    keyboard = [[
        InlineKeyboardButton(
            text="🎮 Play Bert Tap Attack", 
            web_app=WebAppInfo(url=GITHUB_URL)
        )
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Ready to go, {user.first_name}? 🚀\n"
        "Your progress is backed up to Telegram Cloud automatically.",
        reply_markup=reply_markup
    )

def main():
    if not TOKEN:
        logger.error("No BOT_TOKEN found! Set it in your environment variables.")
        return

    # Initialize the Application
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))

    print("Bot is starting up... Ready for Bert Tap Attack.")
    app.run_polling()

if __name__ == '__main__':
    main()