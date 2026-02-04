import os
import tempfile
import time
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

# ===== КЛЮЧИ =====
GEMINI_API_KEY = "AIzaSyB_9YQW0Jy9vAWMRIIb2EAhzd99p0SRAkY"
TELEGRAM_TOKEN = "8259227124:AAEbRbHcrq-Y5N__ETzgu-x5tsdVdsf0aGI"

client = genai.Client(api_key=GEMINI_API_KEY)

IMAGE_MODEL = "gemini-1.5-flash"   # ✅ стабильная модель


# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Gemini AI Bot\n\n"
        "✍️ Напиши текст — сделаю изображение\n"
        "🖼 Отправь фото + подпись — изменю фото\n"
        "🎬 /video текст — видео (нужен биллинг)"
    )


# ===== SAFE GENERATE =====
def safe_generate(**kwargs):
    for attempt in range(5):
        try:
            return client.models.generate_content(**kwargs)
        except Exception as e:
            if "429" in str(e):
                time.sleep(25)
            else:
                raise e
    raise Exception("Превышена квота Gemini API")


# ===== TEXT → IMAGE =====
async def text_to_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text("🎨 Генерирую изображение...")

    try:
        response = safe_generate(
            model=IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                with open(path, "wb") as f:
                    f.write(part.inline_data.data)

                await update.message.reply_photo(photo=path)
                return

        await update.message.reply_text("Не удалось получить изображение")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


# ===== IMAGE → IMAGE =====
async def edit_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.caption:
        await update.message.reply_text("Добавь описание к фото")
        return

    await update.message.reply_text("🛠 Изменяю изображение...")

    photo = update.message.photo[-1]
    file = await photo.get_file()
    img_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
    await file.download_to_drive(img_path)

    img = Image.open(img_path)

    try:
        response = safe_generate(
            model=IMAGE_MODEL,
            contents=[update.message.caption, img],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                out = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                with open(out, "wb") as f:
                    f.write(part.inline_data.data)

                await update.message.reply_photo(out)
                return

        await update.message.reply_text("Не удалось изменить изображение")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


# ===== VIDEO =====
async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Используй: /video описание")
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
        await update.message.reply_text(
            "❌ Видео недоступно без биллинга\n\n" + str(e)
        )


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
