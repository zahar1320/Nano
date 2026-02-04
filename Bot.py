import os
import tempfile
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from google import genai
from google.genai import types
from PIL import Image

# ===== ВСТАВЬ СВОЙ КЛЮЧ =====
GEMINI_API_KEY = "PASTE_NEW_KEY_HERE"
TELEGRAM_TOKEN = "PASTE_TELEGRAM_TOKEN"

client = genai.Client(api_key=GEMINI_API_KEY)


# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Gemini AI Bot\n\n"
        "Напиши текст — сделаю фото\n"
        "Отправь фото + подпись — изменю фото\n"
        "Напиши /video текст — сделаю видео"
    )


# ===== TEXT → IMAGE =====
async def text_to_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text

    await update.message.reply_text("🎨 Генерирую изображение...")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(
                    tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                )
                with open(img.filename, "wb") as f:
                    f.write(part.inline_data.data)

                await update.message.reply_photo(photo=img.filename)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


# ===== IMAGE → IMAGE =====
async def edit_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.caption:
        await update.message.reply_text("Добавь описание изменений к фото")
        return

    prompt = update.message.caption
    photo = update.message.photo[-1]

    await update.message.reply_text("🛠 Изменяю изображение...")

    file = await photo.get_file()
    path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
    await file.download_to_drive(path)

    img = Image.open(path)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[prompt, img],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                out = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name

                with open(out, "wb") as f:
                    f.write(part.inline_data.data)

                await update.message.reply_photo(out)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


# ===== VIDEO GENERATION =====
async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)

    if not prompt:
        await update.message.reply_text("Используй /video описание")
        return

    await update.message.reply_text("🎬 Генерирую видео...")

    try:
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=prompt
        )

        video = operation.result().generated_videos[0]

        path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

        client.files.download(file=video.video, path=path)

        await update.message.reply_video(video=path)

    except Exception as e:
        await update.message.reply_text(f"Ошибка видео: {e}")


# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("video", generate_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_image))
    app.add_handler(MessageHandler(filters.PHOTO, edit_image))

    print("BOT STARTED")
    app.run_polling()


if __name__ == "__main__":
    main()
