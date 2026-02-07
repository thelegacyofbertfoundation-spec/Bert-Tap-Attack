import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURATION ---
# Replace with your GitHub Pages URL (e.g., https://username.github.io/repo/)
GAME_URL = "https://your-username.github.io/your-repo-name/" 
# Render will pull this from your Environment Variables
TOKEN = os.getenv('BOT_TOKEN')

# Enable logging to monitor bot activity in Render logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends the welcome message and the 'Play' button.
    The game will automatically load progress from Telegram Cloud Storage.
    """
    user_name = update.effective_user.first_name
    
    # Create the button that launches your GitHub-hosted game
    keyboard = [
        [
            InlineKeyboardButton(
                text="🎮 Start Tapping!", 
                web_app=WebAppInfo(url=GAME_URL)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Hi {user_name}! 🚀\n\n"
        "Welcome to your Viral Tapper. Your progress is now "
        "automatically saved to your Telegram account.\n\n"
        "Ready to earn some coins?",
        reply_markup=reply_markup
    )

def main():
    """Starts the bot."""
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing! Check your Render environment variables.")
        return

    # Build the application using your Bot Token
    app = Application.builder().token(TOKEN).build()

    # Handle the /start command
    app.add_handler(CommandHandler("start", start))

    print("Bot is live and running...")

    # drop_pending_updates=True ensures the bot starts clean without 409 Conflicts
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()