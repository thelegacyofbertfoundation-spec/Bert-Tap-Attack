import os
import psycopg
import json
import logging
import time
from collections import defaultdict
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Environment variables
TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://bert-tap-attack-s9db.onrender.com')
PORT = int(os.getenv('PORT', '10000'))

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")

GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

last_sync = defaultdict(float)

def init_db():
    try:
        conn = psycopg.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                id BIGINT PRIMARY KEY, 
                name TEXT, 
                score INTEGER
            )
        """)
        conn.commit()
        c.close()
        conn.close()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error("❌ Database error: %s", e)

def update_db(uid, name, score):
    try:
        conn = psycopg.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("""
            INSERT INTO leaderboard (id, name, score) 
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET name = %s, score = %s
        """, (uid, str(name), int(score), str(name), int(score)))
        conn.commit()
        c.close()
        conn.close()
        logger.info("✅ Score updated: User %s = %s", uid, score)
    except Exception as e:
        logger.error("❌ DB update error: %s", e)
        raise

def get_rank():
    try:
        conn = psycopg.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT name, score FROM leaderboard ORDER BY score DESC LIMIT 10")
        res = c.fetchall()
        c.close()
        conn.close()
        
        if not res:
            return "🏆 No scores yet! Be the first!"
        
        leaderboard_text = "🏆 Global Leaderboard 🏆\n\n"
        medals = ["🥇", "🥈", "🥉"]
        
        for i, row in enumerate(res):
            medal = medals[i] if i < 3 else str(i+1) + "."
            leaderboard_text += medal + " " + row[0] + ": " + "{:,}".format(row[1]) + "\n"
        
        return leaderboard_text
    except Exception as e:
        logger.error("❌ Leaderboard error: %s", e)
        return "❌ Error loading leaderboard"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📩 /start from user %s", update.effective_user.id)
    try:
        keyboard = [[KeyboardButton(text="🕹️ PLAY BERT", web_app=WebAppInfo(url=GITHUB_URL))]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🎮 *Bert Tap Attack* 🎮\n\n"
            "✅ *HOW TO PLAY:*\n"
            "Use the *☰ Menu button* (bottom-left) → Play Game\n\n"
            "*Commands:*\n"
            "/leaderboard - View top players\n"
            "/debug - Check your score",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error("❌ Start error: %s", e)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📊 /leaderboard from user %s", update.effective_user.id)
    await update.message.reply_text(get_rank())

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔧 /debug from user %s", update.effective_user.id)
    try:
        conn = psycopg.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT id, name, score FROM leaderboard ORDER BY score DESC")
        res = c.fetchall()
        c.close()
        conn.close()
        
        if not res:
            await update.message.reply_text("❌ Database is empty!")
        else:
            msg = f"📊 Database Contents ({len(res)} entries):\n\n"
            for row in res:
                msg += f"ID: {row[0]}\nName: {row[1]}\nScore: {row[2]:,}\n\n"
            await update.message.reply_text(msg)
            logger.info("Database has %s entries", len(res))
    except Exception as e:
        logger.error("Debug error: %s", e)
        await update.message.reply_text(f"❌ Error: {e}")

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("=" * 60)
    logger.info("🎯 WEBAPP DATA RECEIVED!")
    logger.info("User: %s (%s)", update.effective_user.first_name, update.effective_user.id)
    
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        score = data.get('score', 0)
        
        logger.info("📊 Score: %s", score)
        
        if not isinstance(score, int) or score < 0:
            await update.message.reply_text("⚠️ Invalid score!")
            return
        
        if score > 10000000:
            logger.warning("🚫 SUSPICIOUS SCORE! User %s tried to submit %s", update.effective_user.id, score)
            await update.message.reply_text("⚠️ Score too high! Maximum 10,000,000 allowed.")
            return
        
        update_db(update.effective_user.id, update.effective_user.first_name, score)
        await update.message.reply_text("✅ Score Synced!\n\n" + get_rank())
        logger.info("✅ SUCCESS!")
        
    except Exception as e:
        logger.error("❌ Error: %s", e)
        await update.message.reply_text("❌ Sync failed")
    
    logger.info("=" * 60)

def main():
    port_env = os.getenv('PORT')
    
    logger.info("=" * 60)
    logger.info("🚀 BERT TAP BOT - WEBHOOK MODE (PRO)")
    logger.info("🔍 DEBUG INFO:")
    logger.info("  - PORT env var: %s (type: %s)", port_env, type(port_env))
    logger.info("  - All env vars with 'PORT': %s", {k: v for k, v in os.environ.items() if 'PORT' in k.upper()})
    
    if port_env:
        actual_port = int(port_env)
        logger.info("  ✅ Using Render-assigned PORT: %s", actual_port)
    else:
        actual_port = 10000
        logger.warning("  ⚠️  PORT not set by Render! Using fallback: %s", actual_port)
        logger.warning("  ⚠️  This may cause 404 errors!")
    
    logger.info("Webhook: %s", WEBHOOK_URL)
    logger.info("=" * 60)
    
    init_db()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("debug", debug_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    webhook_url = WEBHOOK_URL + "/" + TOKEN
    
    logger.info("🔗 Starting webhook server...")
    logger.info("🌐 Webhook URL: %s", webhook_url)
    logger.info("🔌 Listening on 0.0.0.0:%s", actual_port)
    logger.info("📍 Webhook path: /%s", TOKEN)
    
    app.run_webhook(
        listen="0.0.0.0",
        port=actual_port,
        url_path=TOKEN,
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()
