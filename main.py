import os
import aiohttp
from messages import messages 
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "7012457237:AAFvXS3AJt4Y6KM_oHuMYMqb-WWEl6OenDs"
PRIVATE_GROUP_LINK = "https://t.me/+5naTkmoBWK9hMWVi"
API_URL = "https://script.google.com/macros/s/AKfycbweEBeUWzuPmLykeKIDOyGVfNvKcJ4F1ChaJ07oV3YYLIp8OXqMnVLEMDSMBIbdjc-qog/exec"

application = ApplicationBuilder().token(TOKEN).build()

LANGUAGE, PHONE, FULL_NAME = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language_buttons = [
        [KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇰🇿 Қазақша")]
    ]
    reply_markup = ReplyKeyboardMarkup(language_buttons, one_time_keyboard=True)
    await update.message.reply_text("🔤 Выберите язык:", reply_markup=reply_markup)
    return LANGUAGE

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = 'kz' if update.message.text == "🇰🇿 Қазақша" else 'ru'
    context.user_data['language'] = language
    button = KeyboardButton(messages[language]['share_contact'], request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True)
    await update.message.reply_text(messages[language]['start'], reply_markup=reply_markup)
    return PHONE

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_contact = update.message.contact
    if user_contact:
        phone_number = user_contact.phone_number
        context.user_data["phone_number"] = phone_number
        language = context.user_data.get('language', 'kz')
        await update.message.reply_text(messages[language]['thank_you'])
        return FULL_NAME
    else:
        language = context.user_data.get('language', 'kz')
        await update.message.reply_text(messages[language]['request_contact'])

async def handle_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_full_name = update.message.text
    phone_number = context.user_data.get("phone_number")
    language = context.user_data.get('language', 'kz')
    loading_message = await update.message.reply_text(messages[language]['loading'])
    submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    success = await send_post_request(user_full_name, phone_number, submitted_at)
    await loading_message.delete()
    if success:
        await update.message.reply_text(messages[language]['success'].format(user_full_name, phone_number))
        await update.message.reply_text(messages[language]['join_link'].format(PRIVATE_GROUP_LINK))
    else:
        await update.message.reply_text(messages[language]['error'])

    return ConversationHandler.END

async def send_post_request(full_name: str, phone_number: str, submitted_at: str) -> bool:
    form_data = {
        "Аты-жөні": full_name,
        "Номер телефона": phone_number,
        "Жіберілген Уақыты": submitted_at,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data=form_data) as response:
            if response.status == 200:
                print("Деректер сәтті жіберілді.")
                return True
            else:
                print(f"Қате: {response.status}")
                return False

async def webhook(request):
    """Vercel-compatible webhook handler."""
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"status": "ok"}


def main():
    application.bot.set_webhook("https://your-vercel-app.vercel.app/api/webhook")
    application.run_polling()

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language_selection)],
        PHONE: [MessageHandler(filters.CONTACT, handle_contact)],
        FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name)],
    },
    fallbacks=[],
    allow_reentry=True,
)
application.add_handler(conversation_handler)


if __name__ == '__main__':
    main()
