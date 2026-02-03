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
STATUS_URL = "https://api.nanobananaapi.ai/api/v1/nanobanana/record-info"

# ===== Команда /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 NanoBanana бот готов!\n"
        "Напиши текст — сделаю картинку\n"
        "Или отправь фото с подписью — отредактирую её"
    )

# ===== Генерация из текста =====
async def generate_text_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text("🎨 Отправляю задачу на генерацию...")

    headers = {
        "Authorization": f"Bearer {NANOBANANO_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "type": "TEXTTOIAMGE",
        "numImages": 1,
        "image_size": "1:1",
        "callBackUrl": ""
    }

    try:
        res = requests.post(GENERATE_URL, headers=headers, json=data)
        result = res.json()

        if not res.ok or result.get("code") != 200:
            await update.message.reply_text(f"Ошибка API: {result.get('msg','Unknown')}")
            return

        task_id = result["data"].get("taskId")
        await update.message.reply_text(f"✅ Задача отправлена! Task ID: {task_id}\n🕒 Жду готовности...")

        # ===== Ожидаем результат =====
        for _ in range(20):
            time.sleep(2)
            status_res = requests.get(
                STATUS_URL,
                params={"taskId": task_id},
                headers={"Authorization": f"Bearer {NANOBANANO_API_KEY}"}
            )
            status_data = status_res.json()
            if status_res.ok and status_data.get("code") == 200:
                success_flag = status_data["data"].get("successFlag")
                if success_flag == 1:
                    image_url = status_data["data"]["response"].get("resultImageUrl")
                    if image_url:
                        await update.message.reply_photo(image_url)
                        return
                elif success_flag in (2, 3):
                    await update.message.reply_text("❌ Ошибка генерации.")
                    return

        await update.message.reply_text("⌛ Картинка пока не готова, попробуй позже.")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# ===== Редактирование фото (Image-to-Image) =====
async def edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.caption:
        await update.message.reply_text("Добавь текст к фото для редактирования")
        return

    prompt = update.message.caption
    photo = update.message.photo[-1]

    await update.message.reply_text("🛠 Отправляю задачу на редактирование фото...")

    # Скачиваем фото
    file = await photo.get_file()
    file_path = await file.download_to_drive()

    headers = {
        "Authorization": f"Bearer {NANOBANANO_API_KEY}"
    }

    files = {
        "image": open(file_path, "rb")
    }

    data = {
        "prompt": prompt,
        "type": "IMAGETOIMAGE",
        "numImages": 1,
        "image_size": "1:1",
        "callBackUrl": ""
    }

    try:
        res = requests.post(GENERATE_URL, headers=headers, files=files, data=data)
        result = res.json()

        if not res.ok or result.get("code") != 200:
            await update.message.reply_text(f"Ошибка API: {result.get('msg','Unknown')}")
            return

        task_id = result["data"].get("taskId")
        await update.message.reply_text(f"✅ Задача на редактирование отправлена! Task ID: {task_id}\n🕒 Жду готовности...")

        # ===== Ожидаем результат =====
        for _ in range(20):
            time.sleep(2)
            status_res = requests.get(
                STATUS_URL,
                params={"taskId": task_id},
                headers={"Authorization": f"Bearer {NANOBANANO_API_KEY}"}
            )
            status_data = status_res.json()
            if status_res.ok and status_data.get("code") == 200:
                success_flag = status_data["data"].get("successFlag")
                if success_flag == 1:
                    image_url = status_data["data"]["response"].get("resultImageUrl")
                    if image_url:
                        await update.message.reply_photo(image_url)
                        return
                elif success_flag in (2, 3):
                    await update.message.reply_text("❌ Ошибка редактирования.")
                    return

        await update.message.reply_text("⌛ Фото пока не готово, попробуй позже.")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# ===== Запуск бота =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_text_image))
    app.add_handler(MessageHandler(filters.PHOTO, edit_photo))
    print("BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
