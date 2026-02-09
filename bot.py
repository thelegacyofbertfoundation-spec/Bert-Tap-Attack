import os
import sqlite3
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonDefault
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATABASE ---import os
import sqlite3
import json
import logging
import html
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonDefault
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

def update_leaderboard(user_id, username, score):
    # Escape HTML characters in usernames to prevent crashes
    safe_name = html.escape(username)
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)", 
              (user_id, safe_name, int(score)))
    conn.commit()
    conn.close()

def get_leaderboard_text():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    players = c.fetchall()
    conn.close()
    
    if not players:
        return "<b>🏆 Global Leaderboard 🏆</b>\n\nNo scores recorded yet!"
    
    text = "<b>🏆 Global Leaderboard 🏆</b>\n\n"
    for i, (name, s) in enumerate(players, 1):
        medal = "🥇 " if i == 1 else "🥈 " if i == 2 else "🥉 " if i == 3 else f"{i}. "
        # Use HTML bold tags for reliability
        text += f"{medal}<b>{name}</b>: {s:,} 💰\n"
    return text

# --- 3. HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Ensure any ghost menu buttons are cleared
    await context.bot.set_chat_menu_button(chat_id=update.effective_chat.id, menu_button=MenuButtonDefault())
    
    keyboard = [[KeyboardButton(text="🥊 Launch Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Hey <b>{user.first_name}</b>! 🥊\n\nLaunch Bert and Sync your score to rank up!",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual leaderboard command - Now using HTML parser for stability."""
    logger.info("Leaderboard command received.")
    await update.message.reply_text(get_leaderboard_text(), parse_mode='HTML')

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes score data from the game."""
    logger.info(">>> SYNC SIGNAL RECEIVED <<<")
    try:
        if update.effective_message.web_app_data:
            data = json.loads(update.effective_message.web_app_data.data)
            user = update.effective_user
            update_leaderboard(user.id, user.first_name, int(data.get('score', 0)))
            # Respond with HTML leaderboard
            await update.message.reply_text(f"✅ Sync Successful!\n\n{get_leaderboard_text()}", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Sync error: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling update:", exc_info=context.error)

# --- 4. START ---
if __name__ == '__main__':
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    # Register commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
    
    # Log errors
    app.add_error_handler(error_handler)
    
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)