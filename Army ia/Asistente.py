import gradio as gr
import pandas as pd
from groq import Groq

client = Groq(api_key="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")

df_global = None

def cargar_csv(archivo):
    global df_global
    try:
        df_global = pd.read_csv(archivo.name)
        return "✅ Archivo CSV cargado correctamente. Ya puedes hacer preguntas."
    except Exception as e:
        return f"❌ Error al cargar el archivo: {str(e)}"

def responder_pregunta_stream(pregunta):
    global df_global
    if df_global is None:
        yield "⚠️ Primero debes cargar un archivo CSV."
        return

    # Construir contexto claro y conciso
    contexto = (
        "Eres un asistente especializado en análisis de datos. "
        "Responde de manera directa y concisa sin explicaciones innecesarias. "
        "Evita repetir la pregunta del usuario. Solo da la respuesta precisa.\n\n"
        f"Fragmento del CSV:\n{df_global.head(3).to_string(index=False)}\n\n"
        f"Columnas: {', '.join(df_global.columns)}\n\n"
        f"Pregunta: {pregunta}"
    )

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "Responde con precisión, de forma directa, y sin rodeos."},
                {"role": "user", "content": contexto}
            ],
            temperature=0.3,
            top_p=0.8,
            max_completion_tokens=300,
            stream=True,
        )

        respuesta = ""
        for chunk in completion:
            token = chunk.choices[0].delta.content or ""
            respuesta += token
            yield respuesta

    except Exception as e:
        yield f"❌ Error al consultar Groq: {str(e)}"

# Interfaz mejorada con estilo moderno
with gr.Blocks(css="body { background-color: #f9f9f9; }") as interfaz:
    with gr.Row():
        gr.Markdown(
            """
            <h1 style='text-align: center;'>🤖 🇵🇪 Causatron para CSV</h1>
            <p style='text-align: center;'>Sube tu archivo CSV y haz preguntas en lenguaje natural.</p>
            """
        )

    with gr.Row():
        archivo_csv = gr.File(label="📎 Sube tu archivo CSV", file_types=[".csv"])
        boton_cargar = gr.Button("📥 Cargar archivo")
        salida_carga = gr.Textbox(label="", interactive=False)

    with gr.Row():
        entrada_pregunta = gr.Textbox(label="💬 Pregunta sobre los datos", placeholder="Ejemplo: ¿Cuántas filas hay?", lines=2)
        boton_preguntar = gr.Button("🤖 Preguntar")

    salida_respuesta = gr.Textbox(label="🧠 Respuesta del asistente", interactive=False, lines=10)

    boton_cargar.click(fn=cargar_csv, inputs=[archivo_csv], outputs=[salida_carga])
    boton_preguntar.click(fn=responder_pregunta_stream, inputs=[entrada_pregunta], outputs=[salida_respuesta])

interfaz.launch()
