import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Gateway Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# ESTILO
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background:
            radial-gradient(circle at 85% 10%, rgba(0, 255, 200, 0.08), transparent 28%),
            radial-gradient(circle at 10% 80%, rgba(140, 0, 255, 0.10), transparent 30%),
            #05070b;
        color: #e8edf7;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #080b12;
        border-right: 1px solid rgba(0, 255, 200, 0.18);
    }

    /* Tipografía */
    h1, h2, h3 {
        letter-spacing: 0.5px;
    }

    .neon-title {
        font-size: 42px;
        font-weight: 800;
        color: #f5f7ff;
        text-shadow:
            0 0 8px rgba(0, 255, 200, 0.55),
            0 0 22px rgba(0, 255, 200, 0.20);
        margin-bottom: 0;
    }

    .subtitle {
        color: #8d9ab3;
        font-size: 15px;
        margin-top: 4px;
        margin-bottom: 25px;
    }

    /* Cards */
    .metric-card {
        background: linear-gradient(145deg, #0d111a, #080b11);
        border: 1px solid rgba(0, 255, 200, 0.22);
        border-radius: 14px;
        padding: 18px 20px;
        min-height: 105px;
        box-shadow: 0 0 20px rgba(0, 255, 200, 0.04);
    }

    .metric-label {
        color: #8995aa;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1.3px;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 800;
        margin-top: 6px;
        color: #00ffd5;
        text-shadow: 0 0 12px rgba(0, 255, 213, 0.35);
    }

    .metric-secondary {
        color: #b38cff;
        font-size: 12px;
        margin-top: 4px;
    }

    /* Bloques de gráficos */
    .chart-box {
        background: #090d14;
        border: 1px solid rgba(160, 120, 255, 0.22);
        border-radius: 14px;
        padding: 12px;
        margin-top: 8px;
    }

    .section-title {
        color: #ffffff;
        font-size: 20px;
        font-weight: 700;
        margin: 28px 0 8px 0;
    }

    .section-accent {
        color: #00ffd5;
    }

    /* Status */
    .status-online {
        color: #00ffd5;
        font-weight: 700;
    }

    .status-warning {
        color: #ffd166;
        font-weight: 700;
    }

    .status-offline {
        color: #ff5c8a;
        font-weight: 700;
    }

    /* Botones */
    .stButton > button {
        border: 1px solid rgba(0, 255, 213, 0.35);
        background: #0b1018;
        color: #00ffd5;
        border-radius: 9px;
    }

    .stButton > button:hover {
        border-color: #00ffd5;
        color: #ffffff;
        box-shadow: 0 0 14px rgba(0, 255, 213, 0.20);
    }

    /* Tabla */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(0, 255, 213, 0.15);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 GATEWAY")
    st.caption("MCI · Monitorización IoT")

    st.markdown("---")
    pagina = st.radio(
        "NAVEGACIÓN",
        ["Overview", "Gateways", "Devices", "Datos", "Configuración"],
        index=0,
    )

    st.markdown("---")
    st.caption("Estado del sistema")
    st.markdown('<span class="status-online">● SISTEMA ONLINE</span>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="neon-title">GATEWAY CONTROL CENTER</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Panel de monitorización y análisis · MCI / IoT / LoRaWAN</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# MÉTRICAS — PLACEHOLDERS
# ─────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        '<div class="metric-card"><div class="metric-label">Gateways</div>'
        '<div class="metric-value">03</div><div class="metric-secondary">2 online · 1 standby</div></div>',
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        '<div class="metric-card"><div class="metric-label">Devices</div>'
        '<div class="metric-value">128</div><div class="metric-secondary">Último registro: hace 2 min</div></div>',
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        '<div class="metric-card"><div class="metric-label">Uplinks</div>'
        '<div class="metric-value">98.7%</div><div class="metric-secondary">Disponibilidad</div></div>',
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        '<div class="metric-card"><div class="metric-label">Alertas</div>'
        '<div class="metric-value">04</div><div class="metric-secondary">2 requieren revisión</div></div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────
# GRÁFICAS DE BORRADOR
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">MONITOREO <span class="section-accent">EN TIEMPO REAL</span></div>', unsafe_allow_html=True)

left, right = st.columns(2)

# Datos de ejemplo para reemplazar posteriormente
rng = np.random.default_rng(7)
time = pd.date_range("2026-10-01 08:00", periods=24, freq="h")
signal_1 = 70 + np.cumsum(rng.normal(0, 1.2, len(time)))
signal_2 = 55 + np.cumsum(rng.normal(0, 1.0, len(time)))

with left:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.caption("📈 Señal / tráfico")
    st.line_chart(pd.DataFrame({"Gateway A": signal_1}, index=time))
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.caption("📶 Calidad de comunicación")
    st.line_chart(pd.DataFrame({"RSSI": signal_2}, index=time))
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">DATOS <span class="section-accent">DEL SISTEMA</span></div>', unsafe_allow_html=True)

c1, c2 = st.columns([1.3, 1])

with c1:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.caption("Estado de dispositivos")
    df_status = pd.DataFrame({
        "Gateway": ["Gateway A", "Gateway B", "Gateway C", "Gateway D"],
        "Ubicación": ["Invernadero 01", "Invernadero 02", "Reservorio", "Taller"],
        "Estado": ["ONLINE", "ONLINE", "WARNING", "OFFLINE"],
        "Devices": [42, 37, 31, 18],
    })
    st.dataframe(df_status, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.caption("Distribución de eventos")
    events = pd.DataFrame({
        "Tipo": ["Uplink", "Downlink", "Warning", "Error"],
        "Cantidad": [820, 146, 32, 7],
    }).set_index("Tipo")
    st.bar_chart(events)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("App Gateway · Plantilla de dashboard · Datos mostrados únicamente como ejemplo.")
