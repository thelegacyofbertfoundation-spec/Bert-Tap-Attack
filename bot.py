import os
import sqlite3
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonWebApp
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATABASE LOGIC ---
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
    # Using INSERT OR REPLACE to ensure the score actually updates
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
    
    if not players:
        return "🏆 **Global Leaderboard** 🏆\n\nNo scores yet! Click Sync & Rank in the game to be first."
    
    text = "🏆 **Global Leaderboard** 🏆\n\n"
    for i, (name, s) in enumerate(players, 1):
        text += f"{i}. **{name}**: {s:,} 💰\n"
    return text

# --- 3. BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonWebApp(text="🕹️ Play Bert", web_app=WebAppInfo(url=GITHUB_URL))
    )
    keyboard = [[KeyboardButton(text="🎮 Play Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "✅ **Bot Online**\nType /leaderboard to check rankings after you sync!",
        reply_markup=reply_markup
    )

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_leaderboard_text(), parse_mode='Markdown')

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the automatic signal when the game closes."""
    logger.info("--- ATTEMPTING TO PROCESS WEB_APP_DATA ---")
    try:
        # We check if the data exists before trying to load it
        if update.effective_message.web_app_data:
            raw_data = update.effective_message.web_app_data.data
            logger.info(f"RAW DATA RECEIVED: {raw_data}")
            
            data = json.loads(raw_data)
            user = update.effective_user
            score = int(data.get('score', 0))
            
            update_leaderboard(user.id, user.first_name, score)
            logger.info(f"SUCCESS: Saved {score} for {user.first_name}")
            
            await update.message.reply_text(f"✅ Sync Successful!\n\n{get_leaderboard_text()}", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Sync error: {e}")

# --- 4. MAIN ---
if __name__ == '__main__':
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
    app.run_polling(drop_pending_updates=True)