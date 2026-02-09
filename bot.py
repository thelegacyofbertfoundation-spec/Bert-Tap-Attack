import os
import psycopg
import json
import logging
import time
from collections import defaultdict
from aiohttp import web
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonDefault
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Environment variables
TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', '10000'))

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL environment variable not set!")
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
    try:
        await context.bot.set_chat_menu_button(
            chat_id=update.effective_chat.id, 
            menu_button=MenuButtonDefault()
        )
        
        kb = [[KeyboardButton(text="🕹️ PLAY BERT", web_app=WebAppInfo(url=GITHUB_URL))]]
        
        welcome_text = (
            "🎮 Welcome to Bert Tap Attack! 🎮\n\n"
            "Tap Bert's face to earn points!\n"
            "Click the button below to start playing.\n\n"
            "Commands:\n"
            "/leaderboard - View top players\n"
            "/start - Show this message"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        logger.info("User %s started the bot", update.effective_user.id)
    except Exception as e:
        logger.error("Start command error: %s", e)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leaderboard command handler"""
    try:
        await update.message.reply_text(get_rank())
    except Exception as e:
        logger.error("Leaderboard command error: %s", e)
        await update.message.reply_text("❌ Error loading leaderboard")

async def handle_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle score sync from web app"""
    logger.info("Data received from web app")
    
    uid = update.effective_user.id
    now = time.time()
    
    # Rate limiting - 5 second cooldown
    if now - last_sync[uid] < 5:
        await update.message.reply_text("⏳ Please wait 5 seconds before syncing again.")
        return
    
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        score = data.get('score', 0)
        
        # Anti-cheat validation
        if not isinstance(score, int) or score < 0:
            await update.message.reply_text("⚠️ Invalid score detected!")
            logger.warning("Invalid score from user %s: %s", uid, score)
            return
        
        if score > 10000000:
            await update.message.reply_text("⚠️ Score too high! Possible cheating detected.")
            logger.warning("Suspiciously high score from user %s: %s", uid, score)
            return
        
        # Update database
        update_db(uid, update.effective_user.first_name, score)
        last_sync[uid] = now
        
        # Send success message with leaderboard
        await update.message.reply_text("✅ Score Synced Successfully!\n\n" + get_rank())
        logger.info("Successfully synced score for user %s: %s", uid, score)
        
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", e)
        await update.message.reply_text("❌ Invalid data format. Please try again.")
    except Exception as e:
        logger.error("Error handling web app data: %s", e)
        await update.message.reply_text("❌ Sync failed. Please try again.")

async def health_check(request):
    """Health check endpoint for Render"""
    return web.Response(text="OK")

def main():
    """Main function to run the bot"""
    logger.info("=" * 50)
    logger.info("Starting Bert Tap Attack Bot")
    logger.info("Port: %s", PORT)
    logger.info("Webhook URL: %s", WEBHOOK_URL)
    logger.info("=" * 50)
    
    # Initialize database
    init_db()
    
    # Build application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_data))
    
    # Full webhook URL
    webhook_url_full = WEBHOOK_URL + "/" + TOKEN
    
    logger.info("Starting webhook server...")
    logger.info("Listening on: 0.0.0.0:%s", PORT)
    logger.info("Webhook path: /%s", TOKEN)
    logger.info("Full webhook URL: %s", webhook_url_full)
    
    # Create web app for health check
    webserver = web.Application()
    webserver.router.add_get('/', health_check)
    webserver.router.add_get('/health', health_check)
    
    # Run webhook with custom web app
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=webhook_url_full,
        web_app=webserver
    )

if __name__ == '__main__':
    main()
