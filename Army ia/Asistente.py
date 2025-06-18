import gradio as gr
import pandas as pd
from groq import Groq

# Inicializa cliente Groq
client = Groq(api_key="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")

df_global = None  # DataFrame global

# Cargar CSV
def cargar_csv(archivo):
    global df_global
    try:
        df_global = pd.read_csv(archivo.name)
        return "✅ Archivo CSV cargado correctamente."
    except Exception as e:
        return f"❌ Error al cargar CSV: {str(e)}"

# Preguntar con modelo de Groq
def responder_pregunta_stream(pregunta):
    global df_global

    if df_global is None:
        yield "⚠️ Por favor, carga primero un archivo CSV."
        return

    # Construir contexto para el modelo
    contexto = f"""Eres un asistente experto en análisis de datos. El usuario ha subido un archivo CSV.
Estas son las primeras filas del archivo:
{df_global.head(3).to_string(index=False)}

Las columnas son: {', '.join(df_global.columns)}.

Ahora responde la siguiente pregunta:
{pregunta}
"""

    # Llamada en modo streaming
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": contexto}],
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            stream=True
        )

        # Mostrar respuesta progresiva
        respuesta = ""
        for chunk in completion:
            token = chunk.choices[0].delta.content or ""
            respuesta += token
            yield respuesta

    except Exception as e:
        yield f"❌ Error al conectarse con Groq: {str(e)}"

# Interfaz Gradio
with gr.Blocks() as interfaz:
    gr.Markdown("# 🧠 Asistente Virtual con CSV + Groq")
    gr.Markdown("Sube tu archivo CSV y haz preguntas en lenguaje natural. El asistente usa el modelo LLaMA 4 Scout de Groq.")

    archivo_csv = gr.File(label="📎 Cargar archivo CSV", file_types=[".csv"])
    salida_carga = gr.Textbox(label="Estado de carga", interactive=False)

    boton_cargar = gr.Button("📥 Cargar CSV")

    gr.Markdown("### 💬 Pregunta sobre tu CSV:")
    entrada_pregunta = gr.Textbox(label="Pregunta", placeholder="Ejemplo: ¿Qué columnas hay?")
    salida_respuesta = gr.Textbox(label="Respuesta del asistente", interactive=False, lines=10)

    boton_preguntar = gr.Button("🤖 Preguntar")

    # Eventos
    boton_cargar.click(fn=cargar_csv, inputs=[archivo_csv], outputs=[salida_carga])
    boton_preguntar.click(fn=responder_pregunta_stream, inputs=[entrada_pregunta], outputs=[salida_respuesta])

# Ejecutar app
interfaz.launch()
