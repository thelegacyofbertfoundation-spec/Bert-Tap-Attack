import os
import sqlite3
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Replace with your actual GitHub Pages URL
GAME_URL = "https://your-username.github.io/your-repo-name/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)

# --- Database Logic ---
def init_db():
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, score INTEGER, max_e INTEGER, tap_p INTEGER)''')
    conn.commit()
    conn.close()

def get_player(user_id):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute("SELECT score, max_e, tap_p FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res if res else (0, 1000, 1)

def save_player(user_id, score, max_e, tap_p):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute("REPLACE INTO users VALUES (?, ?, ?, ?)", (user_id, score, max_e, tap_p))
    conn.commit()
    conn.close()

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    score, max_e, tap_p = get_player(user_id)
    
    # Passing saved data into the Web App URL
    full_url = f"{GAME_URL}?score={score}&max_energy={max_e}&tap_power={tap_p}"
    
    keyboard = [[InlineKeyboardButton("🐻 Play Bear Tapper", web_app=WebAppInfo(url=full_url))]]
    await update.message.reply_text(
        f"Welcome back! Your balance: 💰 {score}\nTap the button to start poking!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Triggers when user clicks 'Sync & Exit'
    raw_data = update.effective_message.web_app_data.data
    data = json.loads(raw_data)
    user_id = update.effective_user.id
    
    save_player(user_id, data['score'], data['maxEnergy'], data['tapPower'])
    await update.message.reply_text(f"✅ Progress saved! Total: {data['score']} 💰")

# --- Main ---
if __name__ == '__main__':
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_save))
    print("Bot is running...")
    app.run_polling()