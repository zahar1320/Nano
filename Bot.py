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
        "Напиши текст — сделаю картинку"
    )

# ===== Обработка текста =====
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "callBackUrl": ""  # оставляем пустым, т.к. опрашиваем вручную
    }

    try:
        res = requests.post(GENERATE_URL, headers=headers, json=data)
        result = res.json()

        if not res.ok or result.get("code") != 200:
            await update.message.reply_text(f"Ошибка отправки задачи: {result.get('msg', 'Unknown')}")
            return

        task_id = result["data"].get("taskId")
        await update.message.reply_text(f"✅ Задача отправлена! Task ID: {task_id}\n🕒 Жду готовности...")

        # ===== Ожидание результата =====
        for _ in range(20):  # опрос до ~40 секунд
            time.sleep(2)

            # Запрос статуса
            status_res = requests.get(
                STATUS_URL,
                params={"taskId": task_id},
                headers={"Authorization": f"Bearer {NANOBANANO_API_KEY}"}
            )

            status_data = status_res.json()
            if status_res.ok and status_data.get("code") == 200:
                # successFlag: 0 = GENERATING, 1 = SUCCESS
                success_flag = status_data["data"].get("successFlag")
                if success_flag == 1:
                    # результат
                    image_url = status_data["data"]["response"].get("resultImageUrl")
                    if image_url:
                        await update.message.reply_photo(image_url)
                        return
                elif success_flag in (2, 3):
                    await update.message.reply_text("❌ Ошибка генерации.")
                    return

        await update.message.reply_text("⏳ Картинка пока не готова, попробуй позже.")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# ===== Запуск бота =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

    print("BOT STARTED")
    app.run_polling()


if __name__ == "__main__":
    main()

