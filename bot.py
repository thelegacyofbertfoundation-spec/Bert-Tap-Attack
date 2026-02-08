import os
import sqlite3
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonWebApp
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

def get_leaderboard_text():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    players = c.fetchall()
    conn.close()
    if not players: return "🏆 **Global Leaderboard** 🏆\n\nNo scores yet! Sync to be first."
    text = "🏆 **Global Leaderboard** 🏆\n\n"
    for i, (name, s) in enumerate(players, 1):
        text += f"{i}. **{name}**: {s:,} 💰\n"
    return text

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Refreshes launchers."""
    user = update.effective_user
    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonWebApp(text="🕹️ Play Bert", web_app=WebAppInfo(url=GITHUB_URL))
    )
    keyboard = [[KeyboardButton(text="🎮 Play Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("✅ **Bot Online (V3.2)**\nLaunch and sync your score!", reply_markup=reply_markup)

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming data."""
    logger.info(">>> DATA RECEIVED <<<")
    try:
        raw_data = update.effective_message.web_app_data.data
        data = json.loads(raw_data)
        user = update.effective_user
        update_leaderboard(user.id, user.first_name, int(data['score']))
        await update.message.reply_text(f"✅ Sync Successful!\n\n{get_leaderboard_text()}", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Sync error: {e}")

if __name__ == '__main__':
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
    app.run_polling(drop_pending_updates=True)