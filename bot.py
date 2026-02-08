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
    """Sends an INLINE keyboard button (required for sendData to work)"""
    user = update.effective_user
    
    # CRITICAL FIX: Use InlineKeyboard instead of ReplyKeyboard or MenuButton
    keyboard = [[InlineKeyboardButton(
        text="🎮 Play Bert Tap Attack",
        web_app=WebAppInfo(url=GITHUB_URL)
    )]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Hey {user.first_name}! 🥊\n\n"
        f"Tap the button below to launch the game.\n"
        f"Use 'Sync & Rank' inside the game to save your score!",
        reply_markup=reply_markup
    )

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes 'Sync & Rank' data and displays the Global Leaderboard."""
    logger.info(">>> DATA RECEIVED FROM GAME <<<")
    try:
        if update.effective_message.web_app_data:
            raw_data = update.effective_message.web_app_data.data
            data = json.loads(raw_data)
            user = update.effective_user
            
            logger.info(f"User {user.first_name} (ID: {user.id}) synced score: {data['score']}")
            
            update_leaderboard(user.id, user.first_name, int(data['score']))
            
            top_players = get_top_10()
            lb_text = "🏆 **Global Leaderboard** 🏆\n\n"
            for i, (name, s) in enumerate(top_players, 1):
                lb_text += f"{i}. {name}: {s:,} 💰\n"
            
            await update.message.reply_text(lb_text, parse_mode='Markdown')
            logger.info("Leaderboard sent successfully")
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        await update.message.reply_text("❌ Sync failed. Please try again!")

# --- EXECUTION ---
if __name__ == '__main__':
    init_db()
    if not TOKEN:
        logger.error("BOT_TOKEN is missing!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
        
        logger.info("Bot starting with polling...")
        app.run_polling(drop_pending_updates=True)