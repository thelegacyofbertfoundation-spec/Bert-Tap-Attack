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
    user = update.effective_user
    # We clear the URL of old data to force the app to use CloudStorage
    keyboard = [[InlineKeyboardButton("🎮 Play Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    await update.message.reply_text(
        f"Welcome {user.first_name}! 🚀\nTap the button to start poking Bert!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves score to the Global Leaderboard when user syncs."""
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user = update.effective_user
        
        # Save to our backend leaderboard
        update_leaderboard(user.id, user.first_name, int(data['score']))
        
        # Build Leaderboard Text
        top_players = get_top_10()
        leaderboard_text = "🏆 **Global Leaderboard** 🏆\n\n"
        for i, (name, score) in enumerate(top_players, 1):
            leaderboard_text += f"{i}. {name}: {score:,} 💰\n"
            
        await update.message.reply_text(leaderboard_text, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Sync failed: {e}")

if __name__ == '__main__':
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
    print("Bert Bot is Live...")
    app.run_polling()