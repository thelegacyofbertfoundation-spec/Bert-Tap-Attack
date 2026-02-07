import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURATION ---
# The official Bert-Tap-Attack GitHub Pages URL
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

# Setup logging to catch errors in Render logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the launcher button with the updated GitHub link."""
    user = update.effective_user
    
    # Launcher button for the Bert-Tap-Attack Mini App
    keyboard = [[
        InlineKeyboardButton(
            text="🎮 Launch Bert Tap Attack", 
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

    print("Bert Tap Bot is starting up... Ready for Bert Tap Attack.")
    app.run_polling()

if __name__ == '__main__':
    main()