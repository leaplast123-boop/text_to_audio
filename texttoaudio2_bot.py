import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from gtts import gTTS
from pypdf import PdfReader

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Pull token from environment variable (Render environment setup)
TOKEN = os.environ.get('8862637342:AAEM1uPKtBSMrSNsKXfy8wwLORPyd55Z7C0')

def text_to_speech_khmer(text, chat_id):
    audio_path = f"audiobook_{chat_id}.mp3"
    
    # Generate audio directly using Google TTS for Khmer ('km')
    tts = gTTS(text=text, lang='km', slow=False)
    tts.save(audio_path)
    
    return audio_path

# Handler for direct text messages
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id

    await update.message.reply_text("🎙️ Generating Khmer audio...")

    try:
        audio_path = text_to_speech_khmer(user_text, chat_id)
        with open(audio_path, 'rb') as audio_file:
            await context.bot.send_audio(chat_id=chat_id, audio=audio_file, title="Khmer Text Clip")
        os.remove(audio_path)
    except Exception as e:
        await update.message.reply_text("An error occurred.")
        print(f"Error: {e}")

# Handler for uploaded pages/files (.txt or .pdf)
async def handle_document(update: Update, context: ContextTypes.DEFAULT_Type):
    document = update.message.document
    chat_id = update.message.chat_id
    file_name = document.file_name.lower()

    await update.message.reply_text(f"📥 Receiving page/file: {file_name}...")

    try:
        # Download file from Telegram
        file = await context.bot.get_file(document.file_id)
        file_path = f"temp_{chat_id}_{file_name}"
        await file.download_to_drive(file_path)

        extracted_text = ""

        # Handle Plain Text Files (.txt)
        if file_name.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()

        # Handle PDF Files (.pdf)
        elif file_name.endswith('.pdf'):
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        else:
            await update.message.reply_text("❌ Please upload a .txt or .pdf file only.")
            os.remove(file_path)
            return

        # Clean up temporary downloaded file
        os.remove(file_path)

        if not extracted_text.strip():
            await update.message.reply_text("❌ No readable text found in this file.")
            return

        await update.message.reply_text(f"🎙️ Converting {file_name} to audio...")

        # Convert text to speech all at once
        audio_path = text_to_speech_khmer(extracted_text, chat_id)

        with open(audio_path, 'rb') as audio_file:
            await context.bot.send_audio(
                chat_id=chat_id, 
                audio=audio_file, 
                title=file_name,
                performer="AI Audiobook Reader"
            )

        os.remove(audio_path)
        await update.message.reply_text("✅ Done!")

    except Exception as e:
        await update.message.reply_text("❌ An error occurred while processing the file.")
        print(f"Error: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Listen to both direct text messages and uploaded files
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Cloud Audiobook Bot is running...")
    app.run_polling()