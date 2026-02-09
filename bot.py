import os
import psycopg
import json
import logging
import time
from collections import defaultdict
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization error: %s", e)

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
        logger.info("Updated score for user %s: %s", uid, score)
    except Exception as e:
        logger.error("Database update error: %s", e)
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
            name = row[0]
            score = row[1]
            medal = medals[i] if i < 3 else str(i+1) + "."
            leaderboard_text += medal + " " + name + ": " + "{:,}".format(score) + "\n"
        
        return leaderboard_text
    except Exception as e:
        logger.error("Leaderboard fetch error: %s", e)
        return "❌ Error loading leaderboard"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("START command from user %s", update.effective_user.id)
    try:
        # KEYBOARD BUTTON (not inline) - this is the key!
        keyboard = [[KeyboardButton(text="🕹️ PLAY BERT", web_app=WebAppInfo(url=GITHUB_URL))]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True,  # Make it smaller
            one_time_keyboard=False  # Keep it visible
        )
        
        welcome_text = (
            "🎮 Bert Tap Attack 🎮\n\n"
            "Click the 🕹️ PLAY BERT button below to start!\n\n"
            "Commands:\n"
            "/leaderboard - View rankings\n"
            "/start - Show this message"
        )
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        logger.info("START sent to user %s", update.effective_user.id)
    except Exception as e:
        logger.error("Start error: %s", e)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("LEADERBOARD from user %s", update.effective_user.id)
    try:
        await update.message.reply_text(get_rank())
    except Exception as e:
        logger.error("Leaderboard error: %s", e)

async def handle_score_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle score messages sent from WebApp"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    
    # Check if this is a score update message
    if '#score_' in text and '🎮 SCORE UPDATE' in text:
        logger.info("=" * 60)
        logger.info("📊 Score message received from %s", update.effective_user.first_name)
        
        try:
            # Extract score from hashtag
            score_tag = [word for word in text.split() if word.startswith('#score_')]
            if score_tag:
                score = int(score_tag[0].replace('#score_', ''))
                logger.info("Extracted score: %s", score)
                
                # Validate
                if score < 0 or score > 10000000:
                    await update.message.reply_text("⚠️ Invalid score!")
                    return
                
                # Save to database
                update_db(update.effective_user.id, update.effective_user.first_name, score)
                await update.message.reply_text("✅ Score Saved to Leaderboard!\n\n" + get_rank())
                logger.info("✅ Score saved successfully")
                
        except Exception as e:
            logger.error("Error parsing score: %s", e)

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("=" * 60)
    logger.info("🎯 WEBAPP DATA RECEIVED!")
    logger.info("User: %s (%s)", update.effective_user.first_name, update.effective_user.id)
    logger.info("=" * 60)
    
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        score = data.get('score', 0)
        
        logger.info("📊 Score: %s", score)
        
        if not isinstance(score, int) or score < 0:
            await update.message.reply_text("⚠️ Invalid score!")
            return
        
        if score > 10000000:
            await update.message.reply_text("⚠️ Score too high!")
            return
        
        update_db(update.effective_user.id, update.effective_user.first_name, score)
        await update.message.reply_text("✅ Score Synced Successfully!\n\n" + get_rank())
        logger.info("✅ Score saved: %s", score)
        
    except Exception as e:
        logger.error("❌ Error: %s", e)
        await update.message.reply_text("❌ Sync failed")

def main():
    logger.info("=" * 60)
    logger.info("🚀 Bert Tap Attack Bot Starting (POLLING)")
    logger.info("=" * 60)
    
    init_db()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_score_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    logger.info("✅ Handlers registered")
    logger.info("=" * 60)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
