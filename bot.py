import os
import sqlite3
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

# Enable detailed logging to track the "Sync" signal
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

def update_leaderboard(user_id, username, score):
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)", 
              (user_id, username, int(score)))
    conn.commit()
    conn.close()

def get_top_10():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    data = c.fetchall()
    conn.close()
    return data

# --- 3. BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the required Reply Keyboard button."""
    user = update.effective_user
    
    # This button MUST be a KeyboardButton for tg.sendData() to work
    keyboard = [[KeyboardButton(
        text="🎮 Play Bert Tap Attack",
        web_app=WebAppInfo(url=GITHUB_URL)
    )]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Hey {user.first_name}! 🥊\n\nLaunch the game using the button below your text bar.\n"
        "This button enables the 'Sync & Rank' feature!",
        reply_markup=reply_markup
    )

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers when the game calls tg.sendData()"""
    logger.info(">>> WEB APP DATA RECEIVED <<<")
    try:
        if update.effective_message.web_app_data:
            raw_data = update.effective_message.web_app_data.data
            data = json.loads(raw_data)
            user = update.effective_user
            
            logger.info(f"User {user.first_name} synced score: {data['score']}")
            
            # Update Database
            update_leaderboard(user.id, user.first_name, int(data['score']))
            
            # Show Leaderboard
            top_players = get_top_10()
            lb_text = "🏆 **Global Leaderboard** 🏆\n\n"
            for i, (name, s) in enumerate(top_players, 1):
                lb_text += f"{i}. {name}: {s:,} 💰\n"
            
            await update.message.reply_text(lb_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Sync failed in Python: {e}")

# --- 4. MAIN RUN ---
if __name__ == '__main__':
    init_db()
    if not TOKEN:
        logger.error("BOT_TOKEN is missing!")
    else:
        # Building the application
        app = Application.builder().token(TOKEN).build()
        
        # Registering handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
        
        print("Bot is live. Conflict prevention (drop_updates) active.")
        # drop_pending_updates=True prevents conflict errors on Render
        app.run_polling(drop_pending_updates=True)