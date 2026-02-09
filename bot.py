import os
import sqlite3
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonDefault
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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
              (user_id, str(username), int(score)))
    conn.commit()
    conn.close()

def get_leaderboard_text():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    players = c.fetchall()
    conn.close()
    if not players: return "🏆 Global Leaderboard 🏆\n\nNo scores yet!"
    text = "🏆 Global Leaderboard 🏆\n\n"
    for i, (name, s) in enumerate(players, 1):
        text += f"{i}. {name}: {s:,} 💰\n"
    return text

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"/start from {user.first_name}")
    await context.bot.set_chat_menu_button(chat_id=update.effective_chat.id, menu_button=MenuButtonDefault())
    keyboard = [[KeyboardButton(text="🥊 Launch Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Welcome {user.first_name}! 🥊\n\nUse the BIG button below to play!", reply_markup=reply_markup)

async def handle_any_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The HEARTBEAT: Logs every update Telegram sends."""
    logger.info(f"Update received: {update}")
    if update.effective_message and update.effective_message.web_app_data:
        data = json.loads(update.effective_message.web_app_data.data)
        user = update.effective_user
        update_leaderboard(user.id, user.first_name, int(data.get('score', 0)))
        await update.message.reply_text(f"✅ Sync Successful!\n\n{get_leaderboard_text()}")

if __name__ == '__main__':
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", lambda u, c: u.message.reply_text(get_leaderboard_text())))
    
    # Broadest possible listener for WebApp data
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_any_update))
    
    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)