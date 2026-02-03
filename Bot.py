import time
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)

# ===== ТОКЕНЫ =====
TELEGRAM_TOKEN = "8259227124:AAEbRbHcrq-Y5N__ETzgu-x5tsdVdsf0aGI"
NANOBANANO_API_KEY = "997e12baa9752221c7a98e7482fa5cd7"

GENERATE_URL = "https://api.nanobananaapi.ai/api/v1/nanobanana/generate"
STATUS_URL = "https://api.nanobananaapi.ai/api/v1/nanobanana/status"

# ===== Команда /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 NanoBanana бот готов!\n\n"
        "Напиши текст — сделаю картинку"
    )

# ===== Генерация картинки =====
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
        "callBackUrl": ""  # оставляем пустым
    }

    # Отправляем задачу
    try:
        res = requests.post(GENERATE_URL, headers=headers, json=data)
        result = res.json()

        if res.ok and result.get('code') == 200:
            task_id = result['data']['taskId']
            await update.message.reply_text(f"✅ Задача отправлена! Task ID: {task_id}\nЖду готовности картинки...")

            # ===== Ожидаем готовность =====
            for _ in range(20):  # опрашиваем до 20 раз (~40 секунд)
                st = requests.post(STATUS_URL, headers=headers, json={"taskId": task_id})
                st_data = st.json()

                if st.ok and st_data.get('code') == 200:
                    status = st_data['data'].get('status')
                    if status == "completed":
                        img_url = st_data['data'].get('imageUrl')
                        if img_url:
                            await update.message.reply_photo(img_url)
                            return
                    elif status == "failed":
                        await update.message.reply_text("❌ Задача не удалась.")
                        return

                time.sleep(2)  # ждём 2 секунды

            await update.message.reply_text("⌛ Картинка пока не готова, попробуй позже.")
        else:
            await update.message.reply_text(f"Ошибка API: {result.get('msg','Unknown error')}")
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
