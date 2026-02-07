import os
import sqlite3
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
# Replace this with your actual GitHub Pages URL (ensure it ends with /)
GAME_URL = "https://your-username.github.io/your-repo-name/" 
TOKEN = os.getenv('BOT_TOKEN')

# Setup logging to see detailed errors in Render logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- DATABASE LOGIC ---
def init_db():
    """Initializes the SQLite database to store player stats."""
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, score INTEGER, max_e INTEGER, tap_p INTEGER)''')
    conn.commit()
    conn.close()

def get_player(user_id):
    """Retrieves a player's data or returns defaults if they are new."""
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute("SELECT score, max_e, tap_p FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res if res else (0, 1000, 1)

def save_player(user_id, score, max_e, tap_p):
    """Saves or updates player data in the database."""
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute("REPLACE INTO users VALUES (?, ?, ?, ?)", (user_id, score, max_e, tap_p))
    conn.commit()
    conn.close()

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the welcome message and the 'Play' button with saved data."""
    user_id = update.effective_user.id
    score, max_e, tap_p = get_player(user_id)
    
    # Passing saved database values into the Game URL as parameters
    full_url = f"{GAME_URL}?score={score}&max_energy={max_e}&tap_power={tap_p}"
    
    keyboard = [[InlineKeyboardButton("🎮 Open Game", web_app=WebAppInfo(url=full_url))]]
    
    await update.message.reply_text(
        f"Welcome back! Your current balance: 💰 {score}\nReady to start earning?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles data sent back from the 'Sync & Exit' button in the Mini App."""
    try:
        raw_data = update.effective_message.web_app_data.data
        data = json.loads(raw_data)
        user_id = update.effective_user.id
        
        save_player(user_id, data['score'], data['maxEnergy'], data['tapPower'])
        
        await update.message.reply_text(f"✨ Progress synced! Current balance: {data['score']} coins.")
    except Exception as e:
        logging.error(f"Error saving data: {e}")
        await update.message.reply_text("❌ There was an error syncing your progress.")

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    # Ensure the database exists before starting
    init_db()
    
    # Build the application
    app = Application.builder().token(TOKEN).build()
    
    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_save))
    
    print("Bot is starting...")
    
    # drop_pending_updates=True prevents the '409 Conflict' error
    app.run_polling(drop_pending_updates=True)