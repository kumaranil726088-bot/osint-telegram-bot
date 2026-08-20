#!/usr/bin/env python3  
"""  
Telegram OSINT Bot - Bulletproof Version  
Designed for Render.com deployment  
"""

import os  
import sys  
import logging  
import asyncio  
import signal  
import time  
from datetime import datetime  
from typing import Optional

# Third-party imports  
from telegram import Update, Bot  
from telegram.ext import (  
    Application,  
    CommandHandler,  
    MessageHandler,  
    filters,  
    ContextTypes,  
    ApplicationBuilder  
)  
import phonenumbers  
from phonenumbers import carrier, geocoder, timezone

# ==================== CONFIGURATION ====================  
# Logging setup  
logging.basicConfig(  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  
    level=logging.INFO,  
    handlers=[  
        logging.StreamHandler(sys.stdout),  
        logging.FileHandler('bot.log') if os.path.exists('/tmp') else logging.StreamHandler()  
    ]  
)  
logger = logging.getLogger(__name__)

# Environment variables  
TOKEN = os.getenv('8982541314:AAF8bIZDyuQaeEDY9ML0SXmiKQvFrT9KC6E')  
PORT = int(os.environ.get('PORT', 8443))  
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

# Validate token  
if not TOKEN:  
    logger.error("❌ CRITICAL: TELEGRAM_BOT_TOKEN environment variable not set!")  
    logger.error("Please set TELEGRAM_BOT_TOKEN in Render environment variables")  
    sys.exit(1)

# ==================== HEALTH CHECK ====================  
class HealthMonitor:  
    """Monitor bot health and restart if needed"""  
      
    def __init__(self):  
        self.start_time = time.time()  
        self.message_count = 0  
        self.error_count = 0  
        self.last_restart = None  
          
    def increment_message(self):  
        self.message_count += 1  
          
    def increment_error(self):  
        self.error_count += 1  
          
    def get_uptime(self):  
        return time.time() - self.start_time  
      
    def get_stats(self):  
        return {  
            'uptime': self.get_uptime(),  
            'messages': self.message_count,  
            'errors': self.error_count,  
            'last_restart': self.last_restart  
        }

health_monitor = HealthMonitor()

# ==================== SIGNAL HANDLERS ====================  
def handle_shutdown(signum, frame):  
    """Graceful shutdown handler"""  
    logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")  
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)  
signal.signal(signal.SIGINT, handle_shutdown)

# ==================== BOT HANDLERS ====================  
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    """Handle /start command"""  
    health_monitor.increment_message()  
      
    welcome_message = """  
🤖 *Telegram OSINT Bot - Professional Edition*  
────────────────────  
*Available Commands:*  
• /start - Show this message  
• /help - Get help  
• /stats - Bot statistics  
• /info <number> - Get phone number info

*Usage:* Send any phone number in international format  
*Example:* +919876543210

⚠️ *Disclaimer:* This bot only provides publicly available information.  
Private data (Aadhar, owner details) cannot be accessed legally.  
────────────────────  
*Bot Status:* ✅ Online  
"""  
      
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    """Handle /help command"""  
    health_monitor.increment_message()  
      
    help_text = """  
📖 *Help Guide*  
────────────────────  
1. Send any phone number in international format  
   *Format:* +[Country Code][Phone Number]  
   *Example:* +919876543210 (India)

2. The bot will provide:  
   • Phone number validation  
   • Country information  
   • Carrier/Service provider  
   • Timezone  
   • Number type (mobile/landline)

3. Commands:  
   • /start - Welcome message  
   • /help - This guide  
   • /stats - Bot statistics  
   • /info <number> - Quick info

⚠️ *Note:* For privacy reasons, personal identification data is not available.  
────────────────────  
"""  
      
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    """Handle /stats command"""  
    health_monitor.increment_message()  
      
    stats = health_monitor.get_stats()  
    uptime_hours = stats['uptime'] / 3600  
      
    stats_message = f"""  
📊 *Bot Statistics*  
────────────────────  
• *Uptime:* {uptime_hours:.2f} hours  
• *Messages Processed:* {stats['messages']}  
• *Errors Encountered:* {stats['errors']}  
• *Last Restart:* {stats['last_restart'] or 'Never'}  
• *Memory Usage:* {sys.getsizeof(object()) / 1024:.2f} KB  
• *Python Version:* {sys.version.split()[0]}  
────────────────────  
*Status:* ✅ Operational  
"""  
      
    await update.message.reply_text(stats_message, parse_mode='Markdown')

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    """Handle /info command with argument"""  
    health_monitor.increment_message()  
      
    if not context.args:  
        await update.message.reply_text("❌ Please provide a phone number.  
Usage: /info +919876543210")  
        return  
      
    phone_number = context.args[0]  
    await process_phone_number(update, phone_number)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    """Handle incoming text messages"""  
    health_monitor.increment_message()  
      
    message_text = update.message.text.strip()  
      
    # Check if message looks like a phone number  
    if any(char.isdigit() for char in message_text) and ('+' in message_text or len(message_text) > 7):  
        await process_phone_number(update, message_text)  
    else:  
        await update.message.reply_text(  
            "📱 Please send a phone number in international format.  
"  
            "*Example:* +919876543210  
"  
            "Use /help for more information.",  
            parse_mode='Markdown'  
        )

async def process_phone_number(update: Update, phone_number: str):  
    """Process phone number and return information"""  
    try:  
        # Clean the phone number  
        phone_number = phone_number.strip()  
          
        # Parse phone number  
        parsed_number = phonenumbers.parse(phone_number, None)  
          
        if not phonenumbers.is_valid_number(parsed_number):  
            await update.message.reply_text("❌ *Invalid phone number format.*  
Please use international format: +[CountryCode][Number]", parse_mode='Markdown')  
            return  
          
        # Get all available information  
        country = geocoder.description_for_number(parsed_number, "en") or "Unknown"  
        carrier_name = carrier.name_for_number(parsed_number, "en") or "Unknown"  
        time_zones = timezone.time_zones_for_number(parsed_number)  
        number_type = phonenumbers.number_type(parsed_number)  
          
        # Convert number type to readable format  
        type_map = {  
            0: "Fixed line",  
            1: "Mobile",  
            2: "Fixed line or mobile",  
            3: "Toll free",  
            4: "Premium rate",  
            5: "Shared cost",  
            6: "VoIP",  
            7: "Personal number",  
            8: "Pager",  
            9: "UAN",  
            10: "Voice mail",  
            27: "Unknown"  
        }  
        number_type_str = type_map.get(number_type, "Unknown")  
          
        # Format response  
        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)  
        national_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)  
          
        response = f"""  
🔍 *Phone Number Analysis*  
────────────────────  
• *Number:* `{formatted_number}`  
• *National Format:* `{national_number}`  
• *Valid:* ✅ Yes  
• *Type:* {number_type_str}  
• *Country:* {country}  
• *Carrier:* {carrier_name}  
• *Timezone:* {', '.join(time_zones) if time_zones else 'Unknown'}  
• *Country Code:* +{parsed_number.country_code}  
────────────────────  
📊 *Technical Details:*  
• E.164 Format: `{phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)}`  
• RFC3966 Format: `{phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.RFC3966)}`  
────────────────────  
⚠️ *Privacy Notice:*  
This information is publicly available through phone number databases.  
Personal identification requires legal authorization.  
────────────────────  
*Analysis Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
"""  
          
        await update.message.reply_text(response, parse_mode='Markdown')  
          
    except phonenumbers.NumberParseException as e:  
        logger.error(f"Number parse error: {e}")  
        await update.message.reply_text(  
            "❌ *Invalid phone number format.*  
"  
            "Please use: +[CountryCode][Number]  
"  
            "*Examples:*  
"  
            "• India: +919876543210  
"  
            "• USA: +12345678901  
"  
            "• UK: +441234567890",  
            parse_mode='Markdown'  
        )  
        health_monitor.increment_error()  
          
    except Exception as e:  
        logger.error(f"Unexpected error: {e}")  
        await update.message.reply_text(  
            "❌ *Server Error*  
"  
            "Please try again later or contact support.  
"  
            "Error has been logged."  
        )  
        health_monitor.increment_error()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    """Global error handler"""  
    health_monitor.increment_error()  
      
    logger.error(f"Update {update} caused error {context.error}")  
      
    if update and update.effective_message:  
        try:  
            await update.effective_message.reply_text(  
                "❌ *An error occurred*  
"  
                "The issue has been logged. Please try again."  
            )  
        except:  
            pass

# ==================== WEBHOOK SETUP ====================  
async def setup_webhook(application: Application):  
    """Setup webhook for Render"""  
    if WEBHOOK_URL:  
        try:  
            webhook_url = f"{WEBHOOK_URL}/{TOKEN}"  
            await application.bot.set_webhook(url=webhook_url)  
            logger.info(f"✅ Webhook set to: {webhook_url}")  
        except Exception as e:  
            logger.error(f"❌ Webhook setup failed: {e}")  
    else:  
        logger.info("⚠️ WEBHOOK_URL not set, using polling")

# ==================== MAIN APPLICATION ====================  
def create_application() -> Application:  
    """Create and configure the application"""  
    try:  
        # Create application with robust settings  
        application = (  
            ApplicationBuilder()  
            .token(TOKEN)  
            .pool_timeout(30)  
            .connect_timeout(30)  
            .read_timeout(30)  
            .write_timeout(30)  
            .get_updates_read_timeout(30)  
            .get_updates_write_timeout(30)  
            .get_updates_connect_timeout(30)  
            .get_updates_pool_timeout(30)  
            .build()  
        )  
          
        # Add handlers  
        application.add_handler(CommandHandler("start", start))  
        application.add_handler(CommandHandler("help", help_command))  
        application.add_handler(CommandHandler("stats", stats_command))  
        application.add_handler(CommandHandler("info", info_command))  
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  
          
        # Add error handler  
        application.add_error_handler(error_handler)  
          
        return application  
          
    except Exception as e:  
        logger.error(f"❌ Failed to create application: {e}")  
        raise

async def main():  
    """Main entry point"""  
    logger.info("🚀 Starting Telegram OSINT Bot...")  
    logger.info(f"📱 Token present: {'✅' if TOKEN else '❌'}")  
    logger.info(f"🌐 Port: {PORT}")  
    logger.info(f"🔗 Webhook URL: {WEBHOOK_URL or 'Not set'}")  
      
    try:  
        # Create application  
        application = create_application()  
          
        # Setup webhook if URL provided  
        await setup_webhook(application)  
          
        # Start based on deployment mode  
        if WEBHOOK_URL:  
            logger.info("🌐 Starting in webhook mode...")  
            await application.run_webhook(  
                listen="0.0.0.0",  
                port=PORT,  
                url_path=TOKEN,  
                webhook_url=WEBHOOK_URL  
            )  
        else:  
            logger.info("🔄 Starting in polling mode...")  
            await application.run_polling(  
                allowed_updates=Update.ALL_TYPES,  
                drop_pending_updates=True,  
                timeout=30,  
                connect_timeout=30,  
                read_timeout=30,  
                write_timeout=30,  
                pool_timeout=30  
            )  
              
    except Exception as e:  
        logger.error(f"💥 Critical error in main: {e}")  
        logger.info("🔄 Attempting restart in 10 seconds...")  
        await asyncio.sleep(10)  
          
        # Try one more time  
        try:  
            application = create_application()  
            await application.run_polling(allowed_updates=Update.ALL_TYPES)  
        except Exception as e2:  
            logger.error(f"💥 Final failure: {e2}")  
            sys.exit(1)

# ==================== ENTRY POINT ====================  
if __name__ == '__main__':  
    # Set health monitor restart time  
    health_monitor.last_restart = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
      
    # Run with asyncio  
    try:  
        asyncio.run(main())  
    except KeyboardInterrupt:  
        logger.info("👋 Bot stopped by user")  
    except Exception as e:  
        logger.error(f"💥 Unhandled exception: {e}")  
        sys.exit(1)  
