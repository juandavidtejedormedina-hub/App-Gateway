import os
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from docx import Document
from google import genai
from google.genai import types
from pypdf import PdfReader

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="Elite Flower Assistant",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Carpeta del repo donde van los documentos (junto a app.py)
DOCS_DIR = Path(__file__).parent / "documentos"
SUPPORTED_EXT = {".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt"}

DEFAULT_MODEL = "gemini-flash-latest"
MAX_CHARS_PER_FILE = 120_000
MAX_CHARS_TOTAL = 600_000


def get_secret(name: str, default=None):
    """Lee de st.secrets o de variables de entorno, sin romperse si no existen."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


API_KEY = get_secret("GEMINI_API_KEY")
MODEL = get_secret("GEMINI_MODEL", DEFAULT_MODEL)

# Si el modelo principal está saturado (503) o no existe (404), se prueban estos en orden.
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
MODELS_TO_TRY = [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]
RETRIES_PER_MODEL = 3

# ============================================================
# ESTILO — DARK / NEON
# ============================================================
st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(circle at 78% 12%, rgba(255, 50, 170, .10), transparent 28%),
        radial-gradient(circle at 15% 75%, rgba(0, 255, 210, .08), transparent 30%),
        #05070b;
    color: #eef2ff;
}
section[data-testid="stSidebar"] {
    background: #080a11;
    border-right: 1px solid rgba(255, 60, 190, .20);
}
.hero { padding: 24px 0 14px 0; }
.hero-title {
    font-size: 40px; font-weight: 850; color: #fff;
    text-shadow: 0 0 12px rgba(255, 55, 190, .35); margin: 0;
}
.hero-sub { color: #929bb0; font-size: 15px; margin-top: 6px; }
.neon { color: #ff4fc3; text-shadow: 0 0 12px rgba(255, 79, 195, .45); }
.cyan { color: #00ffd5; text-shadow: 0 0 12px rgba(0, 255, 213, .35); }
.info-card {
    background: #0b0f17; border: 1px solid rgba(0,255,213,.18);
    border-radius: 12px; padding: 15px;
}
.small-label {
    color: #7f899e; font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px;
}
.big-value { color: #00ffd5; font-size: 25px; font-weight: 800; margin-top: 4px; }
.stButton > button {
    background: #0b1018; color: #00ffd5;
    border: 1px solid rgba(0,255,213,.28); border-radius: 9px;
}
.stButton > button:hover {
    border-color: #00ffd5; box-shadow: 0 0 15px rgba(0,255,213,.18);
}
div[data-testid="stChatMessage"] {
    background: rgba(10,14,22,.82);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 14px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# LECTURA DE DOCUMENTOS (desde la carpeta del repo)
# ============================================================
def _decode_text(data: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def extract_text(path: Path) -> str:
    """Extrae texto de PDF, Word, Excel, CSV o TXT."""
    ext = path.suffix.lower()
    data = path.read_bytes()
    try:
        if ext == ".pdf":
            reader = PdfReader(BytesIO(data))
            pages = []
            for i, page in enumerate(reader.pages, start=1):
                pages.append(f"[Página {i}]\n{page.extract_text() or ''}")
            text = "\n\n".join(pages)

        elif ext == ".docx":
            doc = Document(BytesIO(data))
            parts = [p.text for p in doc.paragraphs if p.text.strip()]
            for t_idx, table in enumerate(doc.tables, start=1):
                parts.append(f"[Tabla {t_idx}]")
                for row in table.rows:
                    parts.append(" | ".join(cell.text.strip() for cell in row.cells))
            text = "\n".join(parts)

        elif ext in (".xlsx", ".xls"):
            sheets = pd.read_excel(BytesIO(data), sheet_name=None)
            parts = []
            for sheet_name, df in sheets.items():
                parts.append(f"[Hoja: {sheet_name}] ({len(df)} filas)")
                parts.append(df.to_csv(index=False))
            text = "\n".join(parts)

        elif ext == ".csv":
            df = pd.read_csv(BytesIO(data), sep=None, engine="python")
            text = f"({len(df)} filas)\n" + df.to_csv(index=False)

        elif ext == ".txt":
            text = _decode_text(data)

        else:
            return f"[Formato {ext} no soportado]"
    except Exception as e:
        return f"[No se pudo leer el archivo: {e}]"

    if len(text) > MAX_CHARS_PER_FILE:
        text = text[:MAX_CHARS_PER_FILE] + "\n[...contenido truncado por tamaño...]"
    return text


def list_document_files() -> list[Path]:
    """Lista los archivos soportados dentro de documentos/ (incluye subcarpetas)."""
    if not DOCS_DIR.exists():
        return []
    files = []
    for p in sorted(DOCS_DIR.rglob("*")):
        if not p.is_file():
            continue
        if p.name.startswith((".", "~$")):  # ocultos y temporales de Word
            continue
        if p.suffix.lower() in SUPPORTED_EXT:
            files.append(p)
    return files


def files_signature(files: list[Path]) -> tuple:
    """Huella de los archivos: si cambia alguno, se vuelve a leer todo."""
    return tuple((str(p), p.stat().st_mtime, p.stat().st_size) for p in files)


@st.cache_data(show_spinner=False)
def load_documents(signature: tuple) -> tuple[str, int, list[str]]:
    """Devuelve (contexto, total_caracteres, nombres_incluidos)."""
    blocks, names, total = [], [], 0
    for path_str, _, _ in signature:
        path = Path(path_str)
        rel = path.relative_to(DOCS_DIR).as_posix()
        text = extract_text(path)
        if total + len(text) > MAX_CHARS_TOTAL:
            blocks.append(f"=== ARCHIVO: {rel} ===\n[Omitido: se alcanzó el límite total]")
            continue
        blocks.append(f"=== ARCHIVO: {rel} ===\n{text}")
        names.append(rel)
        total += len(text)
    return "\n\n".join(blocks), total, names


# ============================================================
# LLAMADA A GEMINI
# ============================================================
def ask_gemini(history: list[dict], area: str, docs_context: str) -> str:
    client = genai.Client(api_key=API_KEY)

    system = (
        "Eres el asistente de Elite Flower, una empresa floricultora. "
        "Responde siempre en español, de forma clara, precisa y concisa. "
        f"El usuario consulta en el área: {area}. "
    )
    if docs_context:
        system += (
            "Responde basándote en los documentos de la empresa que aparecen abajo. "
            "Si la respuesta no está en ellos, dilo claramente en lugar de inventar. "
            "Cuando sea útil, menciona de qué archivo sacaste la información.\n\n"
            "DOCUMENTOS:\n" + docs_context
        )
    else:
        system += (
            "No hay documentos cargados en la base de conocimiento. Puedes responder "
            "con conocimiento general e indicar que no tienes documentos de la empresa."
        )

    # Gemini espera que la conversación empiece con un mensaje del usuario.
    msgs = list(history)
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)

    contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in msgs
    ]

    config = types.GenerateContentConfig(system_instruction=system, temperature=0.3)

    last_error = None
    overload_error = None
    for model_name in MODELS_TO_TRY:
        for attempt in range(RETRIES_PER_MODEL):
            try:
                response = client.models.generate_content(
                    model=model_name, contents=contents, config=config
                )
                return response.text or "No obtuve respuesta del modelo. Intenta reformular la pregunta."
            except Exception as e:
                last_error = e
                msg = str(e)
                if "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    overload_error = e
                    if attempt < RETRIES_PER_MODEL - 1:
                        time.sleep(2 * (attempt + 1))
                        continue
                    break  # agotó reintentos: pasa al siguiente modelo
                if "404" in msg or "NOT_FOUND" in msg:
                    break  # el modelo no existe: pasa al siguiente
                raise  # otro error (llave inválida, etc.)

    raise (overload_error or last_error)


def friendly_error(e: Exception) -> str:
    msg = str(e)
    if "404" in msg or "NOT_FOUND" in msg:
        hint = (
            "Ninguno de los modelos configurados está disponible para tu cuenta. "
            "Agrega en Secrets `GEMINI_MODEL = \"gemini-3.5-flash\"` (o el modelo que "
            "recomiende el detalle técnico de abajo) y reinicia la app."
        )
    elif "503" in msg or "UNAVAILABLE" in msg:
        hint = (
            "Los modelos de Google están saturados en este momento (ya reintenté con "
            "varios modelos). Espera uno o dos minutos y vuelve a preguntar."
        )
    elif "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        hint = "Se alcanzó el límite de uso de la API. Espera un momento e intenta de nuevo."
    elif "403" in msg or "PERMISSION_DENIED" in msg or "API key" in msg or "400" in msg:
        hint = "La API Key es inválida, fue revocada o no tiene permisos. Genera una nueva en Google AI Studio."
    else:
        hint = "Ocurrió un error inesperado."
    return f"⚠️ {hint}\n\n<details><summary>Detalle técnico</summary>\n\n`{msg}`\n\n</details>"


# ============================================================
# CARGA DE DOCUMENTOS
# ============================================================
doc_files = list_document_files()
docs_context, docs_chars, docs_names = ("", 0, [])
if doc_files:
    with st.spinner("Leyendo documentos..."):
        docs_context, docs_chars, docs_names = load_documents(files_signature(doc_files))

# ============================================================
# ESTADO
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hola. Soy el **asistente de Elite Flower**. 🌸\n\n"
                "Ya tengo cargados los documentos de la empresa. "
                "Pregúntame lo que necesites sobre ellos."
            ),
        }
    ]

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🌸 **ELITE FLOWER**")
    st.caption("Asistente inteligente")
    st.markdown("---")

    st.markdown("### 📚 Base de conocimiento")
    if docs_names:
        st.markdown(
            f'<span class="cyan">● {len(docs_names)} documento(s) cargado(s)</span>',
            unsafe_allow_html=True,
        )
        with st.expander("Ver documentos"):
            for n in docs_names:
                st.caption(f"• {n}")
    else:
        st.warning("No hay documentos en la carpeta `documentos/` del repositorio.")

    if st.button("🔄 Recargar documentos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("### Áreas")
    area = st.selectbox(
        "Contexto de consulta",
        [
            "General",
            "Invernaderos",
            "Sensores e IoT",
            "Reservorios",
            "Mantenimiento",
            "Automatización",
            "Energía",
            "Datos y reportes",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Accesos rápidos")
    quick = [
        "Hazme un resumen de los documentos",
        "¿Cuáles son los puntos clave?",
        "Lista los datos o cifras más importantes",
    ]
    for q in quick:
        if st.button(q, use_container_width=True):
            st.session_state.pending_prompt = q

    st.markdown("---")
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = st.session_state.messages[:1]
        st.rerun()

    st.markdown("---")
    if API_KEY:
        st.markdown('<span class="cyan">● IA CONECTADA</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="neon">● SIN API KEY</span>', unsafe_allow_html=True)

# ============================================================
# CABECERA
# ============================================================
st.markdown(
    '<div class="hero">'
    '<div class="hero-title">ELITE FLOWER <span class="neon">AI ASSISTANT</span></div>'
    '<div class="hero-sub">Consulta y analiza los documentos de la empresa con inteligencia artificial</div>'
    "</div>",
    unsafe_allow_html=True,
)

cards = [
    ("DOCUMENTOS", str(len(docs_names)), "Archivos en el repositorio"),
    ("CONTENIDO", f"{docs_chars:,}".replace(",", "."), "Caracteres leídos"),
    ("ÁREA", area, "Contexto activo"),
    ("MODELO", str(MODEL), "Gemini"),
]
cols = st.columns(4)
for col, (label, value, note) in zip(cols, cards):
    with col:
        st.markdown(
            f'<div class="info-card"><div class="small-label">{label}</div>'
            f'<div class="big-value" style="font-size:{"25px" if len(value) < 14 else "17px"}">{value}</div>'
            f'<div style="color:#778197;font-size:11px;margin-top:4px">{note}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# CHAT
# ============================================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

prompt = st.chat_input("Escribe una consulta sobre Elite Flower...")
if not prompt:
    prompt = st.session_state.pop("pending_prompt", None)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not API_KEY:
            answer = (
                "⚠️ No encontré la `GEMINI_API_KEY`. Agrégala en **Settings → Secrets** "
                'de Streamlit Cloud:\n\n```toml\nGEMINI_API_KEY = "tu_llave"\n```'
            )
            st.markdown(answer)
        else:
            with st.spinner("Pensando..."):
                try:
                    answer = ask_gemini(st.session_state.messages, area, docs_context)
                    st.markdown(answer)
                except Exception as e:
                    answer = friendly_error(e)
                    st.markdown(answer, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": answer})

st.markdown("---")
st.caption(f"Elite Flower Assistant · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
