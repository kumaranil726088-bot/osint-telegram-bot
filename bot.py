import os  
import logging  
import sys  
from telegram import Update  
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes  
import phonenumbers  
from phonenumbers import carrier, geocoder, timezone

# Enable logging  
logging.basicConfig(  
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  
level=logging.INFO  
)  
logger = logging.getLogger(__name__)

# Bot token from @botfather  
TOKEN = os.getenv('8982541314:AAF8bIZDyuQaeEDY9ML0SXmiKQvFrT9KC6E')

if not TOKEN:  
logger.error("ERROR: TELEGRAM_BOT_TOKEN environment variable not set!")  
sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):  
"""Send a message when the command /start is issued."""  
await update.message.reply_text(  
'Hello! I am OSINT Bot.  
'  
'Send me a phone number to get information.  
'  
'Format: +919876543210'  
)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):  
"""Send a message when the command /help is issued."""  
await update.message.reply_text(  
'Send me a phone number in international format.  
'  
'Example: +919876543210  
'  
'I will provide available public information.'  
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):  
"""Handle incoming messages."""  
message_text = update.message.text.strip()

try:  
# Parse phone number  
phone_number = phonenumbers.parse(message_text, None)

if not phonenumbers.is_valid_number(phone_number):  
await update.message.reply_text("Invalid phone number format.")  
return

# Get basic information  
country = geocoder.description_for_number(phone_number, "en")  
carrier_name = carrier.name_for_number(phone_number, "en")  
time_zones = timezone.time_zones_for_number(phone_number)

# Format response  
response = f"""  
📱 Phone Number Analysis:  
────────────────────  
• Number: {phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}  
• Valid: ✅ Yes  
• Country: {country}  
• Carrier: {carrier_name or 'Unknown'}  
• Timezone: {', '.join(time_zones) if time_zones else 'Unknown'}  
────────────────────  
⚠️ Note: This bot only provides publicly available information.  
Private data (Aadhar, owner details) cannot be accessed legally.  
"""

await update.message.reply_text(response)

except Exception as e:  
logger.error(f"Error processing message: {e}")  
await update.message.reply_text(  
"Error processing request. Please use format: +919876543210  
"  
"Or use /help for instructions."  
)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  
"""Log errors."""  
logger.error(f"Update {update} caused error {context.error}")

def main():  
"""Start the bot."""  
try:  
# Create application  
application = Application.builder().token(TOKEN).build()

# Add handlers  
application.add_handler(CommandHandler("start", start))  
application.add_handler(CommandHandler("help", help_command))  
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  
application.add_error_handler(error_handler)

# Start bot  
logger.info("Bot starting...")  
application.run_polling(allowed_updates=Update.ALL_TYPES)  
except Exception as e:  
logger.error(f"Bot failed to start: {e}")  
sys.exit(1)

if __name__ == '__main__':  
main()  
