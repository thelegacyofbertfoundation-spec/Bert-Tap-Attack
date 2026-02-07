import os
import sqlite3
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURATION ---
# Replace with your actual GitHub Pages URL
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATABASE LOGIC ---
def init_db():
    """Initializes the leaderboard database."""
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

def update_leaderboard(user_id, username, score):
    """Saves the player's score to the global list."""
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)", 
              (user_id, username, int(score)))
    conn.commit()
    conn.close()

def get_top_10():
    """Retrieves the top 10 players by score."""
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    data = c.fetchall()
    conn.close()
    return data

# --- 3. HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the game launcher."""
    user = update.effective_user
    keyboard = [[InlineKeyboardButton("🎮 Launch Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    
    await update.message.reply_text(
        f"Hey {user.first_name}! 🥊\nReady to rank up? Your progress is saved in the Telegram Cloud.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Catches data from the 'Sync & Rank' button."""
    try:
        # Get raw data from Telegram's WebApp signal
        raw_data = update.effective_message.web_app_data.data
        data = json.loads(raw_data)
        user = update.effective_user
        
        # Save to DB
        update_leaderboard(user.id, user.first_name, data['score'])
        
        # Build the Leaderboard text
        top_players = get_top_10()
        lb_text = "🏆 **Global Leaderboard** 🏆\n\n"
        for i, (name, score) in enumerate(top_players, 1):
            lb_text += f"{i}. {name}: {score:,} 💰\n"
            
        await update.message.reply_text(lb_text, parse_mode='Markdown')
        logger.info(f"Leaderboard updated for {user.first_name}")

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        await update.message.reply_text("❌ Sync Error. Please try again from the game.")

# --- 4. EXECUTION ---
if __name__ == '__main__':
    init_db()
    if not TOKEN:
        logger.error("BOT_TOKEN is missing!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        
        # Listen for any WebApp data sent back
        app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
        
        print("Bot is live. Using drop_pending_updates to prevent Conflicts.")
        app.run_polling(drop_pending_updates=True)