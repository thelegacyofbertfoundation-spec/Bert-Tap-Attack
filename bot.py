import os
import sqlite3
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonWebApp
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATABASE LOGIC ---
def init_db():
    """Ensures the database and table exist."""
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)''')
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def update_leaderboard(user_id, username, score):
    """Saves or updates player score."""
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)", 
              (user_id, username, int(score)))
    conn.commit()
    conn.close()

def get_leaderboard_text():
    """Formats the top 10 players into a message."""
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    players = c.fetchall()
    conn.close()
    
    if not players:
        return "🏆 **Global Leaderboard** 🏆\n\nNo scores recorded yet. Be the first to Sync!"
    
    text = "🏆 **Global Leaderboard** 🏆\n\n"
    for i, (name, s) in enumerate(players, 1):
        text += f"{i}. **{name}**: {s:,} 💰\n"
    return text

# --- 3. BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the Menu Button and sends the Keyboard Button."""
    user = update.effective_user
    
    # Update Menu Button (next to text bar)
    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonWebApp(text="🕹️ Play Bert", web_app=WebAppInfo(url=GITHUB_URL))
    )
    
    keyboard = [[KeyboardButton(text="🎮 Play Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Hey {user.first_name}! 🥊\n\nBuild V2.7 is active.\n"
        "• Tap Bert to earn coins.\n"
        "• Click **Sync & Rank** to save.\n"
        "• Type /leaderboard anytime to see rankings!",
        reply_markup=reply_markup
    )

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explicitly handles the /leaderboard command."""
    logger.info("Manual leaderboard command triggered.")
    await update.message.reply_text(get_leaderboard_text(), parse_mode='Markdown')

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles automatic data sent when the game closes via Sync button."""
    try:
        raw_data = update.effective_message.web_app_data.data
        data = json.loads(raw_data)
        user = update.effective_user
        
        # Update DB
        update_leaderboard(user.id, user.first_name, int(data['score']))
        logger.info(f"Sync Success: {user.first_name} saved {data['score']}")
        
        # Send Leaderboard immediately after sync
        await update.message.reply_text(get_leaderboard_text(), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Sync error: {e}")

# --- 4. MAIN ---
if __name__ == '__main__':
    init_db()
    if not TOKEN:
        logger.error("BOT_TOKEN is missing!")
    else:
        app = Application.builder().token(TOKEN).build()
        
        # Register commands
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
        
        # Listen for WebApp data
        app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
        
        logger.info("Bot is starting up...")
        app.run_polling(drop_pending_updates=True)