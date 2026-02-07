import os
import sqlite3
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURATION ---
# Replace with your actual GitHub Pages URL (Must end in /)
GITHUB_URL = "https://your-username.github.io/your-repo-name/" 
# Replace with your real token from BotFather
TOKEN = os.getenv('BOT_TOKEN')

# Enable logging to catch errors in Render logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATABASE MANAGEMENT ---
def init_db():
    """Creates the player table if it doesn't exist."""
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, score INTEGER, max_e INTEGER, tap_p INTEGER)''')
    conn.commit()
    conn.close()

def get_player(user_id):
    """Retrieves player data or returns defaults if new user."""
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute("SELECT score, max_e, tap_p FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res if res else (0, 1000, 1) # (Score, MaxEnergy, TapPower)

def save_player(user_id, score, max_e, tap_p):
    """Saves or updates player data in the SQLite database."""
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute("REPLACE INTO users VALUES (?, ?, ?, ?)", (user_id, score, max_e, tap_p))
    conn.commit()
    conn.close()

# --- 3. COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the game link with saved data passed as URL parameters."""
    user = update.effective_user
    user_id = user.id
    
    # Load their saved progress from the DB
    score, max_e, tap_p = get_player(user_id)
    
    # Build the personalized URL
    # This ensures the game loads their real score immediately
    full_url = f"{GITHUB_URL}?score={score}&max_energy={max_e}&tap_power={tap_p}"
    
    keyboard = [[
        InlineKeyboardButton(
            text="🎮 Play Bert Tap Attack", 
            web_app=WebAppInfo(url=full_url)
        )
    ]]
    
    await update.message.reply_text(
        f"Hey {user.first_name}! 👋\nYour current balance: 💰 {score}\n\n"
        "Tap the button below to launch the game and start earning!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Catches the JSON data sent from the game's 'Sync' button."""
    try:
        # WebApp sends data as a JSON string
        raw_data = update.effective_message.web_app_data.data
        data = json.loads(raw_data)
        
        user_id = update.effective_user.id
        
        # Save to database
        save_player(user_id, data['score'], data['maxEnergy'], data['tapPower'])
        
        await update.message.reply_text(f"✅ Sync Successful! Your balance: {data['score']} 💰")
    except Exception as e:
        logger.error(f"Save data failed: {e}")

# --- 4. MAIN LOOP ---
if __name__ == '__main__':
    # Initialize DB on startup
    init_db()
    
    # Build the Telegram Application
    app = Application.builder().token(TOKEN).build()
    
    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_save))
    
    print("Bert Tap Bot is starting up...")
    app.run_polling()