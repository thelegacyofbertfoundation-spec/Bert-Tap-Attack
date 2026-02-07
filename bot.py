import os
import sqlite3
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 1. Setup Logging & Token
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv('BOT_TOKEN')
GAME_URL = "https://your-username.github.io/your-repo/" # Update this!

# 2. Database Setup
def init_db():
    conn = sqlite3.connect('game_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, score INTEGER, max_energy INTEGER, tap_power INTEGER)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('game_data.db')
    c = conn.cursor()
    c.execute("SELECT score, max_energy, tap_power FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data if data else (0, 1000, 1)

def save_user(user_id, score, max_energy, tap_power):
    conn = sqlite3.connect('game_data.db')
    c = conn.cursor()
    c.execute("REPLACE INTO users VALUES (?, ?, ?, ?)", (user_id, score, max_energy, tap_power))
    conn.commit()
    conn.close()

# 3. Bot Logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    score, max_e, tap_p = get_user(user_id)
    
    # We pass the saved data into the URL so the game can load it
    personalized_url = f"{GAME_URL}?score={score}&max_energy={max_e}&tap_power={tap_p}"
    
    keyboard = [[InlineKeyboardButton("🎮 Play Now", web_app=WebAppInfo(url=personalized_url))]]
    await update.message.reply_text(
        f"Welcome back! Your current balance: 💰 {score}\nReady to tap?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This triggers when the user clicks "Save & Exit" in the game
    data = json.loads(update.effective_message.web_app_data.data)
    user_id = update.effective_user.id
    
    save_user(user_id, data['score'], data['maxEnergy'], data['tapPower'])
    
    await update.message.reply_text(f"✅ Progress synced! Total: 💰 {data['score']}")

# 4. Main Run
if __name__ == '__main__':
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))
    print("Bot is live...")
    app.run_polling()