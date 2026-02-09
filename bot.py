import os, sqlite3, json, logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonDefault
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
TOKEN = os.getenv('BOT_TOKEN')
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_db(uid, name, score):
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS leaderboard (id INTEGER PRIMARY KEY, name TEXT, score INTEGER)")
    c.execute("INSERT OR REPLACE INTO leaderboard VALUES (?, ?, ?)", (uid, str(name), int(score)))
    conn.commit()
    conn.close()

def get_rank():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("SELECT name, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    res = c.fetchall()
    conn.close()
    return "🏆 Leaderboard 🏆\n\n" + "\n".join([f"{i+1}. {p[0]}: {p[1]:,}" for i, p in enumerate(res)])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_chat_menu_button(chat_id=update.effective_chat.id, menu_button=MenuButtonDefault())
    kb = [[KeyboardButton(text="🕹️ PLAY BERT", web_app=WebAppInfo(url=GITHUB_URL))]]
    await update.message.reply_text("🥊 V5.1 NUCLEAR ONLINE.", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Priority Response Handler."""
    # 1. IMMEDIATE ACKNOWLEDGMENT (Kills the loading circle)
    await update.message.reply_text("✅ Syncing your score...")
    
    # 2. PROCESS DATA
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        update_db(update.effective_user.id, update.effective_user.first_name, data['score'])
        await update.message.reply_text(get_rank())
    except Exception as e:
        logger.error(e)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_data))
    app.run_polling()