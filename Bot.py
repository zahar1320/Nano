import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ===== ТОКЕНЫ =====
TELEGRAM_TOKEN = "8259227124:AAEbRbHcrq-Y5N__ETzgu-x5tsdVdsf0aGI"
NANOBANANO_API_KEY = "997e12baa9752221c7a98e7482fa5cd7"

API_URL = "https://nanobananaapi.ai/v1/generate"  # исправлено


# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 NanoBanano бот готов\n\n"
        "Напиши текст — сделаю картинку\n"
        "Отправь фото + текст — отредактирую"
    )


# ===== ГЕНЕРАЦИЯ ИЗ ТЕКСТА =====
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):

    prompt = update.message.text

    await update.message.reply_text("🎨 Генерирую картинку...")

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {NANOBANANO_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": prompt,
                "size": "1024x1024"
            }
        )

        data = response.json()
        image_url = data.get("image_url")

        if image_url:
            await update.message.reply_photo(image_url)
        else:
            await update.message.reply_text(f"Ошибка генерации: {data}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка генерации: {e}")


# ===== РЕДАКТИРОВАНИЕ ФОТО =====
async def edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.caption:
        await update.message.reply_text("Добавь текст к фото")
        return

    prompt = update.message.caption

    await update.message.reply_text("🛠 Редактирую фото...")

    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = await file.download_to_drive()

        with open(file_path, "rb") as img_file:
            files = {"image": img_file}
            data = {"prompt": prompt, "size": "1024x1024"}

            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {NANOBANANO_API_KEY}"
                },
                data=data,
                files=files
            )

        data = response.json()
        image_url = data.get("image_url")

        if image_url:
            await update.message.reply_photo(image_url)
        else:
            await update.message.reply_text(f"Ошибка редактирования: {data}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка редактирования: {e}")


# ===== ЗАПУСК =====
def main():

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
    app.add_handler(MessageHandler(filters.PHOTO, edit_photo))

    print("BOT STARTED")
    app.run_polling()


if __name__ == "__main__":
    main()
