import os
import sqlite3
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE LOGIC ---
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

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[InlineKeyboardButton("🎮 Launch Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    await update.message.reply_text(
        f"Welcome {user.first_name}! 🥊\n\nTap the button to start poking Bert!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes 'Sync & Rank' data and displays the Global Leaderboard."""
    try:
        raw_data = update.effective_message.web_app_data.data
        data = json.loads(raw_data)
        user = update.effective_user
        
        # 1. Update Leaderboard
        update_leaderboard(user.id, user.first_name, int(data['score']))
        
        # 2. Get Top 10
        top_players = get_top_10()
        lb_text = "🏆 **Global Leaderboard** 🏆\n\n"
        for i, (name, score) in enumerate(top_players, 1):
            lb_text += f"{i}. {name}: {score:,} 💰\n"
            
        await update.message.reply_text(lb_text, parse_mode='Markdown')
        logger.info(f"Leaderboard updated for {user.first_name}")

    except Exception as e:
        logger.error(f"Sync error: {e}")

# --- MAIN RUN ---
if __name__ == '__main__':
    init_db()
    if not TOKEN:
        logger.error("BOT_TOKEN is missing!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        # Listen specifically for the data sent by tg.sendData()
        app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
        
        print("Starting bot. Cleaning old sessions...")
        # drop_pending_updates prevents the Conflict error on restart
        app.run_polling(drop_pending_updates=True)