import os, sqlite3, json, logging, html
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonDefault
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/" 
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DB LOGIC ---
def update_leaderboard(user_id, username, score):
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS leaderboard (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)")
    c.execute("INSERT OR REPLACE INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)", 
              (user_id, str(username), int(score)))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect('bert_data.db')
    c = conn.cursor()
    c.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    players = c.fetchall()
    conn.close()
    if not players: return "🏆 No scores yet!"
    return "🏆 Leaderboard 🏆\n\n" + "\n".join([f"{i+1}. {p[0]}: {p[1]:,}" for i, p in enumerate(players)])

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_chat_menu_button(chat_id=update.effective_chat.id, menu_button=MenuButtonDefault())
    kb = [[KeyboardButton(text="🥊 PLAY BERT", web_app=WebAppInfo(url=GITHUB_URL))]]
    await update.message.reply_text("🥊 V5.0 ONLINE. Use the button to play.", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🛡️ THE SHIELD: This function MUST finish and reply to stop the loading circle."""
    logger.info("Signal received.")
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user = update.effective_user
        update_leaderboard(user.id, user.first_name, data['score'])
        await update.message.reply_text(f"✅ Synced!\n\n{get_leaderboard()}")
    except Exception as e:
        logger.error(f"Error: {e}")
        # Always reply to stop the loading spinner
        await update.message.reply_text("⚠️ Sync finished with errors, but your data was sent.")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", lambda u, c: u.message.reply_text(get_leaderboard())))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_sync))
    app.run_polling(drop_pending_updates=False) # 🛡️ NEVER drop updates!