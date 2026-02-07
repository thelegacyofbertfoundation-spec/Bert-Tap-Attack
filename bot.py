import os
import sqlite3
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
# Your official repository link
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

# Logging setup for Render
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    # Stores user IDs, names, and their highest scores for the leaderboard
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

def update_leaderboard(user_id, username, score):
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)", 
              (user_id, username, score))
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
    """Sends the game launcher. No parameters are passed to prevent 'ghost' scores."""
    user = update.effective_user
    keyboard = [[InlineKeyboardButton("🎮 Launch Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    
    await update.message.reply_text(
        f"Hey {user.first_name}! 🥊\n\nReady to rank up? Your progress is saved in the Telegram Cloud.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Updates the leaderboard and sends it back to the chat."""
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user = update.effective_user
        
        # Save to database
        update_leaderboard(user.id, user.first_name, int(data['score']))
        
        # Format Leaderboard response
        top_players = get_top_10()
        lb_text = "🏆 **Global Leaderboard** 🏆\n\n"
        for i, (name, score) in enumerate(top_players, 1):
            lb_text += f"{i}. {name}: {score:,} 💰\n"
            
        await update.message.reply_text(lb_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Leaderboard Sync Error: {e}")

# --- EXECUTION ---
if __name__ == '__main__':
    init_db()
    if not TOKEN:
        logger.error("ERROR: BOT_TOKEN is missing in Environment Variables!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
        
        print("Bot is live. Conflict prevention (drop_pending_updates) active.")
        # drop_pending_updates=True prevents Conflict errors on Render
        app.run_polling(drop_pending_updates=True)