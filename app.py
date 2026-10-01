import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Elite Flower Assistant",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# ESTILO — DARK / NEON
# ============================================================
st.markdown("""
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
.hero {
    padding: 32px 0 20px 0;
}
.hero-title {
    font-size: 42px;
    font-weight: 850;
    color: #fff;
    text-shadow: 0 0 12px rgba(255, 55, 190, .35);
    margin: 0;
}
.hero-sub {
    color: #929bb0;
    font-size: 15px;
    margin-top: 6px;
}
.neon {
    color: #ff4fc3;
    text-shadow: 0 0 12px rgba(255, 79, 195, .45);
}
.cyan {
    color: #00ffd5;
    text-shadow: 0 0 12px rgba(0, 255, 213, .35);
}
.panel {
    background: linear-gradient(145deg, rgba(15,19,29,.95), rgba(8,10,16,.98));
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 0 30px rgba(0,0,0,.20);
}
.info-card {
    background: #0b0f17;
    border: 1px solid rgba(0,255,213,.18);
    border-radius: 12px;
    padding: 15px;
}
.small-label {
    color: #7f899e;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
.big-value {
    color: #00ffd5;
    font-size: 25px;
    font-weight: 800;
    margin-top: 4px;
}
.stButton > button {
    background: #0b1018;
    color: #00ffd5;
    border: 1px solid rgba(0,255,213,.28);
    border-radius: 9px;
}
.stButton > button:hover {
    border-color: #00ffd5;
    box-shadow: 0 0 15px rgba(0,255,213,.18);
}
div[data-testid="stChatMessage"] {
    background: rgba(10,14,22,.82);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ESTADO DEL CHAT
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hola. Soy el **asistente de Elite Flower**. 🌸\n\n"
                "Puedo servir como punto de entrada para consultar información de "
                "invernaderos, sensores, reservorios, energía, mantenimiento, "
                "automatización y datos. Esta primera versión es un prototipo; "
                "conectaremos las fuentes reales después."
            ),
        }
    ]

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🌸 **ELITE FLOWER**")
    st.caption("Asistente inteligente · Prototipo")

    st.markdown("---")
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
        "¿Qué información tenemos de los invernaderos?",
        "Mostrar estado de sensores",
        "Consultar reservorios",
        "Resumen de mantenimiento",
    ]
    for q in quick:
        if st.button(q, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": q})

    st.markdown("---")
    st.caption("Estado")
    st.markdown('<span class="cyan">● PROTOTIPO ACTIVO</span>', unsafe_allow_html=True)

# ============================================================
# CABECERA
# ============================================================
st.markdown(
    '<div class="hero">'
    '<div class="hero-title">ELITE FLOWER <span class="neon">AI ASSISTANT</span></div>'
    '<div class="hero-sub">Asistente para consulta, análisis y operación de información técnica</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ============================================================
# TARJETAS
# ============================================================
a, b, c, d = st.columns(4)

cards = [
    ("FUENTES", "—", "Pendiente de conectar"),
    ("INVERNADEROS", "—", "Datos reales próximamente"),
    ("SENSORES", "—", "Datos reales próximamente"),
    ("ÚLTIMA ACTUALIZACIÓN", "—", "Sistema en prototipo"),
]

for col, (label, value, note) in zip([a, b, c, d], cards):
    with col:
        st.markdown(
            f'<div class="info-card"><div class="small-label">{label}</div>'
            f'<div class="big-value">{value}</div>'
            f'<div style="color:#778197;font-size:11px;margin-top:4px">{note}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# CHAT
# ============================================================
left, right = st.columns([1.65, 1])

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### 💬 Pregúntale a **<span class='cyan'>Elite Assistant</span>**", unsafe_allow_html=True)
    st.caption(f"Contexto seleccionado: **{area}**")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Escribe una consulta sobre Elite Flower...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Respuesta provisional. Aquí conectaremos el modelo y las fuentes reales.
        response = (
            f"Recibí tu consulta en el contexto **{area}**.\n\n"
            "Esta es una respuesta de demostración. En la siguiente etapa "
            "podemos conectar el asistente con los documentos, bases de datos, "
            "dashboards y registros reales de Elite Flower para que responda "
            "con información verificable."
        )
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### 🧠 ¿Qué podrá hacer?")

    capabilities = [
        ("📊", "Consultar datos", "Buscar información en tablas y registros."),
        ("🌱", "Analizar invernaderos", "Temperatura, humedad, PAR, VPD y variables ambientales."),
        ("📡", "Supervisar IoT", "Sensores, gateways, LoRaWAN y comunicaciones."),
        ("💧", "Reservorios", "Nivel, volumen, porcentaje y comportamiento."),
        ("⚡", "Energía", "Consumo, medición y tendencias."),
        ("🔧", "Mantenimiento", "Históricos, equipos y reportes."),
    ]

    for icon, title, desc in capabilities:
        st.markdown(
            f'<div style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.06)">'
            f'<b>{icon} {title}</b><br>'
            f'<span style="color:#818ba0;font-size:12px">{desc}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# ZONA PARA FUTURAS FUENTES / GRÁFICAS
# ============================================================
st.markdown(
    '<div class="panel">'
    '<h3>🔌 Fuentes de información</h3>'
    '<span style="color:#818ba0">Zona preparada para conectar posteriormente '
    'Excel, SQL, APIs, documentos, ChirpStack, dashboards y otras fuentes.</span>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("---")
st.caption(
    f"Elite Flower Assistant · Prototipo · {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
