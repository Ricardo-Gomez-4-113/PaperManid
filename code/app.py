import streamlit as st
import requests
from pypdf import PdfReader
import io
import os
import json
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
API_URL = "http://127.0.0.1:8000/chat"
st.set_page_config(page_title="Chat Académico", layout="wide")

# Directorio para guardar conversaciones
CONVERSATIONS_DIR = "conversations"
if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

# ============================================================
# ESTILOS
# ============================================================
st.markdown("""
<style>
.chat-container {
    background-color: #2a2a2a;
    padding: 20px;
    border-radius: 12px;
    min-height: 70vh;
    margin-bottom: 100px;
    overflow-y: auto;
}
.user-msg {
    background-color: #3a3a3a;
    padding: 12px 16px;
    border-radius: 10px;
    margin: 8px 0;
    color: #e2e2e2;
    width: fit-content;
    max-width: 80%;
    align-self: flex-end;
    margin-left: auto;
}
.assistant-msg {
    background-color: #1d3d2f;
    padding: 12px 16px;
    border-radius: 10px;
    margin: 8px 0;
    color: #e2e2e2;
    width: fit-content;
    max-width: 80%;
    align-self: flex-start;
}
.input-container {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    background-color: #2b2b2b;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 0 10px rgba(0,0,0,0.5);
    z-index: 1000;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = None

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# ============================================================
# FUNCIONES PARA CONVERSACIONES
# ============================================================
def save_conversation():
    if st.session_state.messages:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{CONVERSATIONS_DIR}/conversation_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump({
                "messages": st.session_state.messages,
                "pdf_text": st.session_state.pdf_text,
                "conversation_history": st.session_state.conversation_history
            }, f)
        st.success(f"Conversación guardada como {filename}")

def load_conversation(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    st.session_state.messages = data["messages"]
    st.session_state.pdf_text = data["pdf_text"]
    st.session_state.conversation_history = data.get("conversation_history", [])
    st.session_state.current_conversation = filename
    st.rerun()

def new_conversation():
    st.session_state.messages = []
    st.session_state.pdf_text = ""
    st.session_state.conversation_history = []
    st.session_state.current_conversation = None
    st.rerun()

def list_conversations():
    files = [f for f in os.listdir(CONVERSATIONS_DIR) if f.endswith(".json")]
    return sorted(files, reverse=True)

# ============================================================
# FUNCION PARA LEER PDF
# ============================================================
def read_pdf(uploaded_file):
    if uploaded_file is None:
        return ""

    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error leyendo PDF: {str(e)}")
        return ""

# ============================================================
# FUNCIÓN PARA MANDAR PREGUNTA A LA API LOCAL
# ============================================================
def ask_api(question, pdf_context=""):
    try:
        # Preparar el historial en formato que la API espera
        history = []
        for msg in st.session_state.conversation_history:
            history.append({"role": msg["role"], "content": msg["content"]})
        
        # Combinar contexto del PDF con la pregunta
        full_question = question
        if pdf_context:
            # Limitar el contexto del PDF para no exceder tokens
            context_preview = pdf_context[:3000] + "..." if len(pdf_context) > 3000 else pdf_context
            full_question = f"Contexto del documento:\n{context_preview}\n\nPregunta: {question}"
        
        payload = {
            "question": full_question,
            "history": history,
            "user_id": "streamlit_user"
        }

        response = requests.post(API_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            return f"⚠️ Error en API ({response.status_code}): {response.text}"

        data = response.json()
        
        if "response" in data:
            return data["response"]
        elif "error" in data:
            return f"⚠️ Error: {data['error']}"
        else:
            return "⚠️ Respuesta inesperada de la API"
            
    except requests.exceptions.ConnectionError:
        return "⚠️ Error: No se puede conectar a la API. Asegúrate de que esté ejecutándose en http://127.0.0.1:8000"
    except requests.exceptions.Timeout:
        return "⚠️ Error: Timeout - La API tardó demasiado en responder"
    except Exception as e:
        return f"⚠️ Error inesperado: {str(e)}"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("📄 Documentos")

    uploaded_pdfs = st.file_uploader(
        "Sube uno o varios PDF",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_pdfs:
        full_text = ""
        for pdf in uploaded_pdfs:
            full_text += read_pdf(pdf)

        st.session_state.pdf_text = full_text
        if full_text.strip():
            st.success(f"PDF procesado correctamente ✔️ ({len(uploaded_pdfs)} archivos, {len(full_text)} caracteres)")
        else:
            st.warning("PDF procesado pero no se pudo extraer texto")

    st.divider()
    st.header("💾 Conversaciones")

    if st.button("Nueva Conversación", use_container_width=True):
        new_conversation()

    if st.button("Guardar Conversación Actual", use_container_width=True):
        save_conversation()

    st.subheader("Conversaciones Guardadas")
    conv_files = list_conversations()
    if conv_files:
        selected_conv = st.selectbox("Selecciona una conversación", conv_files, label_visibility="collapsed")
        if st.button("Cargar Conversación Seleccionada", use_container_width=True):
            load_conversation(os.path.join(CONVERSATIONS_DIR, selected_conv))
    else:
        st.write("No hay conversaciones guardadas.")

# ============================================================
# PANEL DE CHAT
# ============================================================
st.title("🤖 Chat Académico con PDFs")

# Mostrar estado de la conexión
try:
    health_check = requests.get("http://127.0.0.1:8000", timeout=5)
    st.success("✅ Conectado a la API")
except:
    st.error("❌ No se puede conectar a la API. Ejecuta: `python server.py`")

# Mostrar mensajes
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("<div class='assistant-msg'>👋 ¡Hola! Sube un PDF y hazme preguntas sobre su contenido.</div>", unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='user-msg'>👤 {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-msg'>🤖 {msg['content']}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# INPUT CON MANEJO CORRECTO DEL ESTADO
# ============================================================
st.markdown("<div class='input-container'>", unsafe_allow_html=True)

# Usar form para manejar mejor el input
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "Escribe tu mensaje:",
            key="user_input",
            label_visibility="collapsed",
            placeholder="Escribe tu pregunta aquí..."
        )
    with col2:
        submit_button = st.form_submit_button("Enviar")

st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# PROCESAR MENSAJE - FORMA CORRECTA
# ============================================================
if submit_button and user_input.strip():
    # Agregar el mensaje del usuario al historial visual
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Mostrar spinner mientras procesa
    with st.spinner("Procesando tu pregunta..."):
        # Obtener respuesta del modelo
        reply = ask_api(user_input, st.session_state.pdf_text)
        
        # Agregar al historial visual
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Actualizar historial de conversación para la API
        st.session_state.conversation_history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": reply}
        ])
    
    # Recargar la página para mostrar los nuevos mensajes
    st.rerun()