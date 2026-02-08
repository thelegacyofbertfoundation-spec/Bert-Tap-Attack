import os
import sqlite3
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATABASE LOGIC ---
def init_db():
    """Initializes the database file on Render."""
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

def update_leaderboard(user_id, username, score):
    """Saves or updates the player's high score."""
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)", 
              (user_id, username, int(score)))
    conn.commit()
    conn.close()

def get_top_10():
    """Returns the top 10 players by score."""
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
    keyboard = [[KeyboardButton(text="🎮 Play Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Hey {user.first_name}! 🥊\n\nYour progress is now saving! Tap the button below to play and Rank Up!",
        reply_markup=reply_markup
    )

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers when the game calls tg.sendData()"""
    logger.info(">>> SYNC SIGNAL RECEIVED <<<")
    try:
        # 1. Parse the incoming JSON
        raw_data = update.effective_message.web_app_data.data
        data = json.loads(raw_data)
        user = update.effective_user
        current_score = int(data.get('score', 0))
        
        # 2. Update the Database
        update_leaderboard(user.id, user.first_name, current_score)
        logger.info(f"Score {current_score} saved for {user.first_name}")
        
        # 3. Generate Leaderboard Text
        top_players = get_top_10()
        if not top_players:
            lb_text = "🏆 **Global Leaderboard** 🏆\n\nNo scores recorded yet. Be the first!"
        else:
            lb_text = "🏆 **Global Leaderboard** 🏆\n\n"
            for i, (name, s) in enumerate(top_players, 1):
                lb_text += f"{i}. **{name}**: {s:,} 💰\n"
            
        # 4. Send back to the user
        await update.message.reply_text(lb_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Leaderboard Sync Error: {e}")
        await update.message.reply_text("❌ Leaderboard error. Your score was saved to cloud, but ranking failed.")

# --- 4. MAIN RUN ---
if __name__ == '__main__':
    init_db()
    if not TOKEN:
        logger.error("BOT_TOKEN is missing!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        
        # Specifically listens for the StatusUpdate.WEB_APP_DATA filter
        app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
        
        print("Bot is live. Conflict prevention (drop_updates) active.")
        app.run_polling(drop_pending_updates=True)