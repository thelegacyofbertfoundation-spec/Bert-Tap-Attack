from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Replace with the token you got from @BotFather
import os
TOKEN = os.getenv('BOT_TOKEN')
# Replace with your GitHub Pages URL
GAME_URL = 'https://your-username.github.io/viral-tap-game/'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message with a button that opens the Web App."""
    
    # This creates the button that launches your game
    keyboard = [
        [
            InlineKeyboardButton(
                text="🎮 Play Turbo Tapper!", 
                web_app=WebAppInfo(url=GAME_URL)
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Join Channel", 
                url="https://t.me/bertcoincto" # Optional: Link to your news channel
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🚀 **Welcome to Turbo Tapper!**\n\n"
        "Tap the coin, upgrade your power, and climb the leaderboard. "
        "Can you reach Level 100?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def main():
    # Build the bot
    application = Application.builder().token(TOKEN).build()

    # Handle the /start command
    application.add_handler(CommandHandler("start", start))

    # Run the bot until you stop it
    print("Bot is running... Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()