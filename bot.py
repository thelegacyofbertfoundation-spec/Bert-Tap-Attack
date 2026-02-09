import os
import psycopg2
import json
import logging
import time
from collections import defaultdict
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, MenuButtonDefault
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Environment variables
TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 8443))

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL environment variable not set!")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")

GITHUB_URL = "https://thelegacyofbertfoundation-spec.github.io/Bert-Tap-Attack/"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
last_sync = defaultdict(float)

def init_db():
    """Initialize database table"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                id BIGINT PRIMARY KEY, 
                name TEXT, 
                score INTEGER
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

def update_db(uid, name, score):
    """Update user score in database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("""
            INSERT INTO leaderboard (id, name, score) 
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET name = %s, score = %s
        """, (uid, str(name), int(score), str(name), int(score)))
        conn.commit()
        conn.close()
        logger.info(f"Updated score for user {uid}: {score}")
    except Exception as e:
        logger.error(f"Database update error: {e}")
        raise

def get_rank():
    """Get top 10 leaderboard"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT name, score FROM leaderboard ORDER BY score DESC LIMIT 10")
        res = c.fetchall()
        conn.close()
        
        if not res:
            return "🏆 No scores yet! Be the first!"
        
        leaderboard_text = "🏆 Global Leaderboard 🏆\n\n"
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (name, score) in enumerate(res):
            medal = medals[i] if i < 3 else f"{i+1}."
            leaderboard_text += f"{medal} {name}: {score:,}\n"
        
        return leaderboard_text
    except Exception as e:
        logger.error(f"Leaderboard fetch error: {e}")
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
        logger.info(f"User {update.effective_user.id} started the bot")
    except Exception as e:
        logger.error(f"Start command error: {e}")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leaderboard command handler"""
    try:
        await update.message.reply_text(get_rank())
    except Exception as e:
        logger.error(f"Leaderboard command error: {e}")
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
            logger.warning(f"Invalid score from user {uid}: {score}")
            return
        
        if score > 10000000:  # Adjust this limit based on your game
            await update.message.reply_text("⚠️ Score too high! Possible cheating detected.")
            logger.warning(f"Suspiciously high score from user {uid}: {score}")
            return
        
        # Update database
        update_db(uid, update.effective_user.first_name, score)
        last_sync[uid] = now
        
        # Send success message with leaderboard
        await update.message.reply_text(f"✅ Score Synced Successfully!\n\n{get_rank()}")
        logger.info(f"Successfully synced score for user {uid}: {score}")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        await update.message.reply_text("❌ Invalid data format. Please try again.")
    except Exception as e:
        logger.error(f"Error handling web app data: {e}")
        await update.message.reply_text("❌ Sync failed. Please try again.")

def main():
    """Main function to run the bot"""
    logger.info("Starting bot...")
    
    # Initialize database
    init_db()
    
    # Build application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_data))
    
    logger.info(f"Starting webhook on port {PORT}")
    logger.info(f"Webhook URL: {WEBHOOK_URL}/{TOKEN}")
    
    # Run webhook for Render deployment
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
        url_path=TOKEN
    )

if __name__ == '__main__':
    main()