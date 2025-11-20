import streamlit as st
import requests
from pypdf import PdfReader
import os
import json
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
API_URL = "http://127.0.0.1:8000/chat"
st.set_page_config(
    page_title="PaperMind - Asistente Académico", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Directorio para guardar conversaciones
CONVERSATIONS_DIR = "conversations"
if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

# ============================================================
# ESTILOS MEJORADOS
# ============================================================
st.markdown("""
<style>
/* Fondo limpio */
.stApp {
    background-color: #0f1116;
}

/* Header minimalista */
.main-header {
    color: #ffffff;
    text-align: center;
    padding: 0.5rem 0;
    margin-bottom: 1rem;
    border-bottom: 1px solid #333;
}

/* Contenedor del chat - TRANSPARENTE Y CON SCROLL */
.chat-container {
    background-color: transparent !important;
    padding: 20px;
    border-radius: 10px;
    min-height: 50vh;
    max-height: 65vh;
    overflow-y: auto;
    margin-bottom: 80px;
}

/* Mensajes de usuario */
.user-msg {
    background-color: #2563eb;
    padding: 12px 16px;
    border-radius: 15px 15px 5px 15px;
    margin: 10px 0;
    color: white;
    max-width: 70%;
    margin-left: auto;
    font-size: 14px;
    line-height: 1.4;
}

/* Mensajes del asistente */
.assistant-msg {
    background-color: #374151;
    padding: 12px 16px;
    border-radius: 15px 15px 15px 5px;
    margin: 10px 0;
    color: #f3f4f6;
    max-width: 70%;
    font-size: 14px;
    line-height: 1.4;
    border-left: 3px solid #10b981;
}

/* Input field */
.stTextInput input {
    background-color: #0f1116 !important;
    color: white !important;
    border: 1px solid #444 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
}

/* Botón */
.stButton button {
    background-color: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    font-weight: 500 !important;
}

/* Botón de eliminar */
.delete-btn {
    background-color: #dc2626 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}

.delete-btn:hover {
    background-color: #b91c1c !important;
}

/* Sidebar */
.css-1d391kg {
    background-color: #1a1a1a;
}

/* Mensaje de bienvenida */
.welcome-msg {
    background-color: #374151;
    padding: 20px;
    border-radius: 10px;
    color: #d1d5db;
    text-align: center;
    border: 1px solid #4b5563;
    margin: 20px 0;
}

/* Estado de conexión */
.connection-status {
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    display: inline-block;
    margin-bottom: 15px;
}

.status-connected {
    background-color: #065f46;
    color: #34d399;
}

.status-error {
    background-color: #7f1d1d;
    color: #fca5a5;
}

/* Info del documento - más discreto */
.doc-info {
    color: #9ca3af;
    font-size: 14px;
    margin-bottom: 15px;
    padding: 8px 12px;
    background-color: #1f2937;
    border-radius: 6px;
    border-left: 3px solid #3b82f6;
}

/* Contenedor de Streamlit - fondo transparente */
.st-emotion-cache-1vo6xi6 {
    background-color: transparent !important;
}

.st-emotion-cache-467cry {
    background-color: transparent !important;
}

.stMarkdown {
    background-color: transparent !important;
}

[data-testid="stMarkdownContainer"] {
    background-color: transparent !important;
}

/* Scrollbar personalizado */
.chat-container::-webkit-scrollbar {
    width: 6px;
}

.chat-container::-webkit-scrollbar-track {
    background: #1a1a1a;
    border-radius: 3px;
}

.chat-container::-webkit-scrollbar-thumb {
    background: #2563eb;
    border-radius: 3px;
}

.chat-container::-webkit-scrollbar-thumb:hover {
    background: #1d4ed8;
}

/* Espacio para el input fijo */
.main-content {
    padding-bottom: 120px;
}

/* Estilo para items de conversación */
.conversation-item {
    padding: 8px 12px;
    margin: 4px 0;
    background-color: #2d3748;
    border-radius: 6px;
    border: 1px solid #4a5568;
}

.conversation-item:hover {
    background-color: #374151;
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

if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = None

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
        st.success(f"✅ Conversación guardada")
        return filename

def load_conversation(filename):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        st.session_state.messages = data["messages"]
        st.session_state.pdf_text = data["pdf_text"]
        st.session_state.conversation_history = data.get("conversation_history", [])
        st.session_state.current_conversation = filename
        st.rerun()
    except Exception as e:
        st.error(f"Error cargando conversación: {e}")

def new_conversation():
    st.session_state.messages = []
    st.session_state.pdf_text = ""
    st.session_state.conversation_history = []
    st.session_state.current_conversation = None
    st.session_state.show_delete_confirm = None
    st.rerun()

def list_conversations():
    try:
        files = [f for f in os.listdir(CONVERSATIONS_DIR) if f.endswith(".json")]
        return sorted(files, reverse=True)
    except:
        return []

def delete_conversation(filename):
    """Elimina una conversación guardada"""
    try:
        filepath = os.path.join(CONVERSATIONS_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            st.success(f"✅ Conversación eliminada: {filename}")
            st.session_state.show_delete_confirm = None
            st.rerun()
        else:
            st.error(f"❌ Archivo no encontrado: {filename}")
    except Exception as e:
        st.error(f"❌ Error eliminando conversación: {e}")

def delete_all_conversations():
    """Elimina todas las conversaciones guardadas"""
    try:
        files = list_conversations()
        if not files:
            st.warning("No hay conversaciones para eliminar")
            return
        
        deleted_count = 0
        for file in files:
            filepath = os.path.join(CONVERSATIONS_DIR, file)
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted_count += 1
        
        st.success(f"✅ {deleted_count} conversaciones eliminadas")
        st.session_state.show_delete_confirm = None
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error eliminando conversaciones: {e}")

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
        return text.strip()
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
        if pdf_context and pdf_context.strip():
            # Limitar el contexto del PDF para no exceder tokens
            context_preview = pdf_context[:2000] + "..." if len(pdf_context) > 2000 else pdf_context
            full_question = f"Contexto del documento:\n{context_preview}\n\nPregunta: {question}"
        
        payload = {
            "question": full_question,
            "history": history,
            "user_id": "streamlit_user"
        }

        response = requests.post(API_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            return f"❌ Error en API ({response.status_code})"

        data = response.json()
        
        if "response" in data:
            return data["response"]
        elif "error" in data:
            return f"❌ Error: {data['error']}"
        else:
            return "❌ Respuesta inesperada de la API"
            
    except requests.exceptions.ConnectionError:
        return "❌ Error: No se puede conectar a la API. Verifica que esté ejecutándose en http://127.0.0.1:8000"
    except requests.exceptions.Timeout:
        return "❌ Error: Timeout - La API tardó demasiado en responder"
    except Exception as e:
        return f"❌ Error inesperado: {str(e)}"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("📄 Documentos")
    
    uploaded_pdfs = st.file_uploader(
        "Cargar PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Sube uno o varios documentos PDF"
    )

    if uploaded_pdfs:
        with st.spinner("Procesando PDFs..."):
            full_text = ""
            for pdf in uploaded_pdfs:
                full_text += read_pdf(pdf) + "\n\n"

            st.session_state.pdf_text = full_text.strip()
            
            if st.session_state.pdf_text:
                chars_count = len(st.session_state.pdf_text)
                st.success(f"📚 {len(uploaded_pdfs)} PDF(s) cargado(s) - {chars_count} caracteres")
            else:
                st.warning("⚠️ PDFs procesados pero no se pudo extraer texto")

    st.divider()
    
    st.header("💬 Conversaciones")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 Nueva", use_container_width=True):
            new_conversation()
    with col2:
        if st.button("💾 Guardar", use_container_width=True):
            save_conversation()

    # Botón para eliminar todas las conversaciones
    if st.button("🗑️ Eliminar Todas", use_container_width=True, type="secondary"):
        st.session_state.show_delete_confirm = "all"

    # Conversaciones guardadas
    conv_files = list_conversations()
    if conv_files:
        st.subheader("Historial")
        for conv_file in conv_files[:8]:  # Mostrar hasta 8 conversaciones
            display_name = conv_file.replace("conversation_", "").replace(".json", "")
            
            # Crear un contenedor para cada conversación
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"<div class='conversation-item'>{display_name[:18]}...</div>", unsafe_allow_html=True)
            
            with col2:
                if st.button("📂", key=f"load_{conv_file}"):
                    load_conversation(os.path.join(CONVERSATIONS_DIR, conv_file))
            
            with col3:
                if st.button("🗑️", key=f"delete_{conv_file}", type="secondary"):
                    st.session_state.show_delete_confirm = conv_file
    else:
        st.info("No hay conversaciones guardadas")

    # Confirmación para eliminar
    if st.session_state.show_delete_confirm:
        st.divider()
        st.warning("⚠️ Confirmar eliminación")
        
        if st.session_state.show_delete_confirm == "all":
            st.error("¿Estás seguro de que quieres eliminar TODAS las conversaciones? Esta acción no se puede deshacer.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sí, eliminar todo", use_container_width=True):
                    delete_all_conversations()
            with col2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_delete_confirm = None
                    st.rerun()
        else:
            filename = st.session_state.show_delete_confirm
            display_name = filename.replace("conversation_", "").replace(".json", "")
            st.error(f"¿Eliminar la conversación '{display_name}'?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sí, eliminar", use_container_width=True):
                    delete_conversation(filename)
            with col2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_delete_confirm = None
                    st.rerun()

# ============================================================
# PANEL PRINCIPAL
# ============================================================
st.markdown('<div class="main-header"><h1>🤖 PaperMind</h1></div>', unsafe_allow_html=True)

# Estado de conexión
try:
    response = requests.get("http://127.0.0.1:8000", timeout=3)
    st.markdown('<div class="connection-status status-connected">✅ Conectado a la API</div>', unsafe_allow_html=True)
except:
    st.markdown('<div class="connection-status status-error">❌ API no disponible</div>', unsafe_allow_html=True)

# Área del chat CON SCROLL
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class='welcome-msg'>
        <h3>👋 ¡Bienvenido a PaperMind!</h3>
        <p><strong>Para comenzar:</strong></p>
        <p>1. Sube tus PDFs en el panel lateral</p>
        <p>2. Escribe tu pregunta en el campo de abajo</p>
        <p>3. Obtén respuestas basadas en tus documentos</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='user-msg'><strong>Tú:</strong> {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-msg'><strong>Asistente:</strong> {msg['content']}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Mostrar información del PDF cargado de forma más discreta
if st.session_state.pdf_text:
    doc_info = f"📄 Documento cargado ({len(st.session_state.pdf_text)} caracteres)"
    if len(st.session_state.pdf_text) > 2000:
        doc_info += " - Contexto limitado a 2000 caracteres"
    st.markdown(f'<div class="doc-info">{doc_info}</div>', unsafe_allow_html=True)

# ============================================================
# INPUT DE MENSAJES - FIJO EN LA PARTE INFERIOR
# ============================================================
st.markdown("<div class='input-container'>", unsafe_allow_html=True)

with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "Mensaje:",
            key="user_input",
            label_visibility="collapsed",
            placeholder="Escribe tu pregunta aquí..."
        )
    with col2:
        submit_button = st.form_submit_button(
            "Enviar",
            use_container_width=True
        )

st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# PROCESAR MENSAJE
# ============================================================
if submit_button and user_input.strip():
    # Agregar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Obtener respuesta
    with st.spinner("Procesando..."):
        reply = ask_api(user_input, st.session_state.pdf_text)
        
        # Agregar respuesta al historial
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.conversation_history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": reply}
        ])
    
    st.rerun()