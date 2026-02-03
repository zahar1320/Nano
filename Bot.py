import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)

# ===== ТОКЕНЫ =====
TELEGRAM_TOKEN = "8259227124:AAEbRbHcrq-Y5N__ETzgu-x5tsdVdsf0aGI"
NANOBANANO_API_KEY = "997e12baa9752221c7a98e7482fa5cd7"

API_URL = "https://api.nanobananaapi.ai/api/v1/nanobanana/generate"


# ===== Команда /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 NanoBanana бот готов!\n\n"
        "Напиши текст — сделаю картинку\n"
        "Отправь фото + текст — пока работает только текст → картинка"
    )


# ===== Генерация картинки из текста =====
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text("🎨 Генерирую картинку...")

    headers = {
        "Authorization": f"Bearer {NANOBANANO_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "type": "TEXTTOIAMGE",
        "numImages": 1,
        "callBackUrl": ""  # пока оставляем пустым
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        result = response.json()

        if response.ok and result.get('code') == 200:
            task_id = result['data']['taskId']
            await update.message.reply_text(f"✅ Задача отправлена! Task ID: {task_id}\nКартинка скоро будет готова (Callback пока не используется).")
        else:
            await update.message.reply_text(f"Ошибка API: {result.get('msg', 'Unknown error')}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка запроса: {e}")


# ===== Запуск бота =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

    print("BOT STARTED")
    app.run_polling()


if __name__ == "__main__":
    main()
