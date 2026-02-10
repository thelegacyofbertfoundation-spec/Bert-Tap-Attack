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
        c.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                user_id BIGINT PRIMARY KEY,
                referred_by BIGINT,
                energy_boosts INTEGER DEFAULT 0,
                total_referrals INTEGER DEFAULT 0
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
    user_id = update.effective_user.id
    
    # Check for referral code
    if context.args and len(context.args) > 0:
        ref_code = context.args[0]
        if ref_code.startswith('ref_'):
            try:
                referrer_id = int(ref_code.replace('ref_', ''))
                if referrer_id != user_id:  # Can't refer yourself
                    # Check if user is new (not already in referrals table)
                    conn = psycopg.connect(DATABASE_URL)
                    c = conn.cursor()
                    c.execute("SELECT user_id FROM referrals WHERE user_id = %s", (user_id,))
                    existing = c.fetchone()
                    
                    if not existing:
                        # New user - track referral
                        c.execute("""
                            INSERT INTO referrals (user_id, referred_by, energy_boosts) 
                            VALUES (%s, %s, 0)
                        """, (user_id, referrer_id))
                        
                        # Give referrer a reward
                        c.execute("""
                            INSERT INTO referrals (user_id, energy_boosts, total_referrals)
                            VALUES (%s, 1, 1)
                            ON CONFLICT (user_id) DO UPDATE 
                            SET energy_boosts = referrals.energy_boosts + 1,
                                total_referrals = referrals.total_referrals + 1
                        """, (referrer_id,))
                        
                        conn.commit()
                        logger.info("✅ Referral tracked: %s referred by %s", user_id, referrer_id)
                        
                        # Notify referrer about their reward
                        try:
                            await context.bot.send_message(
                                chat_id=referrer_id,
                                text="🎁 *Congratulations!*\n\n"
                                     "Someone used your invite link!\n\n"
                                     "✅ You earned 1 Energy Refill Boost!\n\n"
                                     "Use /boosts to see your rewards or click ⚡ REFILL in the game!",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.error("Could not notify referrer: %s", e)
                    
                    c.close()
                    conn.close()
            except Exception as e:
                logger.error("Referral error: %s", e)
    
    try:
        keyboard = [[KeyboardButton(text="🕹️ PLAY BERT", web_app=WebAppInfo(url=GITHUB_URL))]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🎮 *Bert Tap Attack* 🎮\n\n"
            "✅ *HOW TO PLAY:*\n"
            "Use the *☰ Menu button* (bottom-left) → Play Game\n\n"
            "*Commands:*\n"
            "/leaderboard - View top players\n"
            "/invite - Get your referral link\n"
            "/boosts - Check your energy boosts",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error("❌ Start error: %s", e)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📊 /leaderboard from user %s", update.effective_user.id)
    await update.message.reply_text(get_rank())

async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🎁 /invite from user %s", update.effective_user.id)
    user_id = update.effective_user.id
    bot_username = "berttapbot"
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    try:
        conn = psycopg.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT total_referrals FROM referrals WHERE user_id = %s", (user_id,))
        result = c.fetchone()
        total_refs = result[0] if result else 0
        c.close()
        conn.close()
        
        await update.message.reply_text(
            f"🎁 *Invite Friends & Earn Rewards!*\n\n"
            f"Share your link:\n`{invite_link}`\n\n"
            f"🎯 *Rewards per friend:*\n"
            f"• 60-minute Energy Refill Boost\n\n"
            f"👥 *Your Stats:*\n"
            f"Friends invited: {total_refs}\n\n"
            f"💡 Tap the link above to copy it!",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error("Invite error: %s", e)

async def boosts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("⚡ /boosts from user %s", update.effective_user.id)
    user_id = update.effective_user.id
    
    try:
        conn = psycopg.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT energy_boosts, total_referrals FROM referrals WHERE user_id = %s", (user_id,))
        result = c.fetchone()
        boosts = result[0] if result else 0
        total_refs = result[1] if result else 0
        c.close()
        conn.close()
        
        await update.message.reply_text(
            f"⚡ *Your Energy Boosts*\n\n"
            f"Available: *{boosts}* boost(s)\n"
            f"Total referrals: {total_refs}\n\n"
            f"💡 *How to use:*\n"
            f"Open the game and click the *⚡ REFILL* button to use a boost!\n\n"
            f"🎁 Earn more by inviting friends with /invite",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error("Boosts error: %s", e)

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
        action = data.get('action', 'sync')
        
        if action == 'get_boosts':
            # Send energy boosts to game
            user_id = update.effective_user.id
            conn = psycopg.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute("SELECT energy_boosts FROM referrals WHERE user_id = %s", (user_id,))
            result = c.fetchone()
            boosts = result[0] if result else 0
            c.close()
            conn.close()
            
            await update.message.reply_text(f"⚡ You have {boosts} energy boost(s)!")
            logger.info("Sent boost count: %s", boosts)
            return
        
        elif action == 'use_boost':
            # Use an energy boost
            user_id = update.effective_user.id
            conn = psycopg.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute("SELECT energy_boosts FROM referrals WHERE user_id = %s", (user_id,))
            result = c.fetchone()
            boosts = result[0] if result else 0
            
            if boosts > 0:
                c.execute("""
                    UPDATE referrals 
                    SET energy_boosts = energy_boosts - 1 
                    WHERE user_id = %s
                """, (user_id,))
                conn.commit()
                new_count = boosts - 1
                await update.message.reply_text(
                    f"✅ *Energy Refilled!*\n\n"
                    f"Boosts remaining: {new_count}",
                    parse_mode='Markdown'
                )
                logger.info("Boost used by %s, remaining: %s", user_id, new_count)
            else:
                # Send message that will trigger invite prompt
                await update.message.reply_text(
                    "❌ *No boosts available!*\n\n"
                    "💡 Click OK to share your invite link and earn more boosts!",
                    parse_mode='Markdown'
                )
            
            c.close()
            conn.close()
            return
        
        # Default: sync score
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
    app.add_handler(CommandHandler("invite", invite_command))
    app.add_handler(CommandHandler("boosts", boosts_command))
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
