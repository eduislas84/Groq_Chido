import logging
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

TELEGRAM_TOKEN = "7970488624:AAFI3l8abnIvgMlyda9C5mSwmuScaHjkjaY"
GROQ_API_KEY = "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"

groq_client = Groq(api_key=GROQ_API_KEY)

user_dataframes = {}

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy un bot que te ayuda a hablar con tus datos.\n\n📁 Envíame un archivo CSV y luego haz preguntas sobre él.")

async def recibir_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    archivo = update.message.document
    if archivo.mime_type != 'text/csv':
        await update.message.reply_text("❌ Solo acepto archivos CSV.")
        return

    archivo_path = await archivo.get_file()
    archivo_local = f"{update.effective_user.id}_data.csv"
    await archivo_path.download_to_drive(archivo_local)

    try:
        df = pd.read_csv(archivo_local)
        user_dataframes[update.effective_user.id] = df
        await update.message.reply_text("✅ Archivo CSV cargado correctamente. ¡Ya puedes hacer preguntas!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error al leer el CSV: {e}")

async def responder_pregunta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    df = user_dataframes.get(user_id)

    if df is None:
        await update.message.reply_text("📁 Primero necesitas subir un archivo CSV.")
        return

    pregunta = update.message.text
    contexto = df.head(10).to_string()

    prompt = f"""
Tengo esta tabla de datos:
{contexto}

Y quiero responder la siguiente pregunta sobre ella:
{pregunta}

Responde en base a los datos. Si no puedes, explica por qué.
"""

    try:
        respuesta_llm = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres un experto en análisis de datos."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192"
        )

        respuesta = respuesta_llm.choices[0].message.content
        await update.message.reply_text(f"🤖 {respuesta}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error con el modelo GROQ: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.MimeType("text/csv"), recibir_csv))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), responder_pregunta))

    print("✅ Bot iniciado. Presiona Ctrl+C para detener.")
    app.run_polling()

if __name__ == '__main__':
    main()
