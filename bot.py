import os
import psycopg
import json
import logging
import time
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Environment variables
TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

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

# Rate limiting
last_sync = defaultdict(float)

def init_db():
    """Initialize database table"""
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
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization error: %s", e)

def update_db(uid, name, score):
    """Update user score in database"""
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
        logger.info("Updated score for user %s: %s", uid, score)
    except Exception as e:
        logger.error("Database update error: %s", e)
        raise

def get_rank():
    """Get top 10 leaderboard"""
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
            name = row[0]
            score = row[1]
            medal = medals[i] if i < 3 else str(i+1) + "."
            leaderboard_text += medal + " " + name + ": " + "{:,}".format(score) + "\n"
        
        return leaderboard_text
    except Exception as e:
        logger.error("Leaderboard fetch error: %s", e)
        return "❌ Error loading leaderboard"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    logger.info("START command received from user %s", update.effective_user.id)
    try:
        # Create inline button with WebApp
        keyboard = [[InlineKeyboardButton("🕹️ PLAY BERT", web_app=WebAppInfo(url=GITHUB_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            "🎮 Welcome to Bert Tap Attack! 🎮\n\n"
            "Tap Bert's face to earn points!\n"
            "Click the button below to start playing.\n\n"
            "Commands:\n"
            "/leaderboard - View top players\n"
            "/start - Show this message"
        )
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        logger.info("START response sent to user %s", update.effective_user.id)
    except Exception as e:
        logger.error("Start command error: %s", e)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leaderboard command handler"""
    logger.info("LEADERBOARD command received from user %s", update.effective_user.id)
    try:
        await update.message.reply_text(get_rank())
    except Exception as e:
        logger.error("Leaderboard command error: %s", e)
        await update.message.reply_text("❌ Error loading leaderboard")

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle WebApp data from message"""
    logger.info("=" * 50)
    logger.info("MESSAGE WEBAPP DATA RECEIVED!")
    logger.info("User: %s", update.effective_user.first_name)
    logger.info("=" * 50)
    
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        score = data.get('score', 0)
        
        logger.info("Parsed score: %s", score)
        
        if not isinstance(score, int) or score < 0:
            await update.message.reply_text("⚠️ Invalid score!")
            return
        
        if score > 10000000:
            await update.message.reply_text("⚠️ Score too high!")
            return
        
        update_db(update.effective_user.id, update.effective_user.first_name, score)
        await update.message.reply_text("✅ Score Synced!\n\n" + get_rank())
        
    except Exception as e:
        logger.error("Error handling webapp data: %s", e)
        await update.message.reply_text("❌ Sync failed")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries (including WebApp data)"""
    query = update.callback_query
    
    logger.info("=" * 50)
    logger.info("CALLBACK QUERY RECEIVED!")
    logger.info("User: %s", update.effective_user.first_name)
    logger.info("Data: %s", query.data if query.data else "None")
    
    # Check if this is WebApp data
    if hasattr(query, 'web_app_data') and query.web_app_data:
        logger.info("WebApp data in callback: %s", query.web_app_data)
    logger.info("=" * 50)
    
    await query.answer()

def main():
    """Main function to run the bot"""
    logger.info("=" * 50)
    logger.info("Starting Bert Tap Attack Bot (POLLING MODE)")
    logger.info("=" * 50)
    
    init_db()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("Bot starting in polling mode...")
    logger.info("Handlers registered:")
    logger.info("  - /start")
    logger.info("  - /leaderboard")
    logger.info("  - WebApp data (message)")
    logger.info("  - Callback queries")
    logger.info("=" * 50)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
