import os
import sqlite3
import json
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonDefault
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

def update_leaderboard(user_id, username, score):
    # Clean username for iOS emoji compatibility
    safe_name = username.encode('ascii', 'ignore').decode('ascii') or f"User_{user_id}"
    
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)", 
              (user_id, safe_name, int(score)))
    conn.commit()
    conn.close()

def get_leaderboard_text():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    players = c.fetchall()
    conn.close()
    if not players: return "🏆 **Leaderboard** 🏆\n\nNo scores yet! Sync to rank up."
    
    text = "🏆 **Global Leaderboard** 🏆\n\n"
    for i, (name, s) in enumerate(players, 1):
        # Add medals for top 3
        medal = "🥇 " if i == 1 else "🥈 " if i == 2 else "🥉 " if i == 3 else f"{i}. "
        text += f"{medal}**{name}**: {s:,} 💰\n"
    return text

# --- 3. HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.set_chat_menu_button(chat_id=update.effective_chat.id, menu_button=MenuButtonDefault())
    keyboard = [[KeyboardButton(text="🥊 Launch Bert Tap Attack", web_app=WebAppInfo(url=GITHUB_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Hey {user.first_name}! 🥊\nV3.6-IOS is active. Launch and sync!", reply_markup=reply_markup)

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(">>> SIGNAL DETECTED <<<")
    try:
        if update.effective_message.web_app_data:
            data = json.loads(update.effective_message.web_app_data.data)
            user = update.effective_user
            # Use first_name as primary ranking name
            name = user.first_name if user.first_name else "Fighter"
            update_leaderboard(user.id, name, int(data.get('score', 0)))
            await update.message.reply_text(f"✅ Sync Successful!\n\n{get_leaderboard_text()}", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Sync error: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling update:", exc_info=context.error)

# --- 4. START BOT ---
if __name__ == '__main__':
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
    app.add_error_handler(error_handler)
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)