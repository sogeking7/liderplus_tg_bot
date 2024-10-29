import os
import aiohttp
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "7012457237:AAFvXS3AJt4Y6KM_oHuMYMqb-WWEl6OenDs"
PRIVATE_GROUP_LINK = "https://t.me/+5naTkmoBWK9hMWVi"
API_URL = "https://script.google.com/macros/s/AKfycbweEBeUWzuPmLykeKIDOyGVfNvKcJ4F1ChaJ07oV3YYLIp8OXqMnVLEMDSMBIbdjc-qog/exec"

messages = {
    'kz': {
        'start': '👋 Сәлем! ҰБТ курсына дайындықты бастау үшін, телефон нөміріңізбен бөлісіңіз.',
        'choose_language': '🔤 Тілді таңдаңыз:',
        'thank_you': '🙏 Телефон нөміріңізді бөліскеніңіз үшін рақмет! \nЕнді толық атыңызды жазыңыз:',
        'loading': '⏳ Деректеріңіз жіберілуде...',
        'success': '😊 Рақмет, {}! Сіздің телефон нөміріңіз: {}',
        'join_link': '🔗 Жеке чатқа қосылу үшін, мына сілтемені басыңыз: {}',
        'error': '❌ Деректерді жіберу кезінде қате болды.',
        'request_contact': '📞 Өтініш, контакт ақпаратын бөлісіңіз.',
        'share_contact': '📞 Телефон нөмірімді бөлісейін',
    },
    'ru': {
        'start': '👋 Привет! Чтобы начать подготовку к ЕНТ, поделитесь своим номером телефона.',
        'choose_language': '🔤 Выберите язык:',
        'thank_you': '🙏 Спасибо за то, что поделились своим номером телефона! \nТеперь напишите ваше полное имя:',
        'loading': '⏳ Данные отправляются...',
        'success': '😊 Спасибо, {}! Ваш номер телефона: {}',
        'join_link': '🔗 Нажмите на эту ссылку, чтобы присоединиться к личному чату: {}',
        'error': '❌ Ошибка при отправке данных.',
        'request_contact': '📞 Пожалуйста, поделитесь вашей контактной информацией.',
        'share_contact': '📞 Поделитесь своим номером телефона',
    }
}

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

def main():
    application = ApplicationBuilder().token(TOKEN).build()

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
    application.run_polling()

if __name__ == '__main__':
    main()
