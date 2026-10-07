"""Interfaz visual inicial del espacio de trabajo de Gateways."""

import streamlit as st


GATEWAYS_STYLES = """
<style>
.gw-hero {
    position: relative; overflow: hidden; min-height: 270px;
    display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(250px, .75fr);
    align-items: center; gap: 24px; margin: 25px 0 24px;
    padding: 38px 44px; border-radius: 24px;
    background: linear-gradient(116deg, #0b1822 0%, #07101a 58%, #111126 100%);
    border: 1px solid rgba(255,255,255,.10);
    box-shadow: 0 22px 70px rgba(0,0,0,.25), inset 0 1px rgba(255,255,255,.04);
}
.gw-hero::before {
    content: ""; position: absolute; width: 360px; height: 360px;
    right: -80px; top: -130px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255,79,195,.18), transparent 65%);
    pointer-events: none;
}
.gw-eyebrow { color: #6cf3dc; font-size: 11px; font-weight: 800;
    letter-spacing: .22em; text-transform: uppercase; margin-bottom: 13px; }
.gw-hero h1 { color: #fff; font-size: clamp(34px, 4.1vw, 61px);
    line-height: 1.04; letter-spacing: -.045em; margin: 0 0 16px; font-weight: 800; }
.gw-hero h1 span { color: #ff69c9; }
.gw-hero p { color: #a7b7c5; max-width: 590px; font-size: 16px;
    line-height: 1.6; margin: 0; }
.gw-hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }
.gw-hero-tags span { color: #c8d5df; font-size: 11px; font-weight: 700;
    letter-spacing: .04em; border: 1px solid rgba(255,255,255,.14);
    padding: 7px 11px; border-radius: 50px; background: rgba(255,255,255,.04); }
.gw-radar { position: relative; width: 246px; height: 246px; margin: auto;
    display: grid; place-items: center; border-radius: 50%;
    background: radial-gradient(circle, rgba(0,255,213,.13) 0%,
        rgba(0,255,213,.04) 28%, transparent 69%); }
.gw-ring { position: absolute; border: 1px solid rgba(72,232,208,.25);
    border-radius: 50%; }
.gw-ring.r1 { width: 72px; height: 72px; }
.gw-ring.r2 { width: 150px; height: 150px; }
.gw-ring.r3 { width: 232px; height: 232px; border-style: dashed; }
.gw-radar::before, .gw-radar::after { content: ""; position: absolute;
    background: rgba(91,216,199,.16); }
.gw-radar::before { height: 1px; width: 220px; }
.gw-radar::after { width: 1px; height: 220px; }
.gw-core { z-index: 2; width: 22px; height: 22px; border: 5px solid #052423;
    border-radius: 50%; background: #5ff4d8; box-shadow: 0 0 0 2px #5ff4d8,
    0 0 30px rgba(95,244,216,.65); }
.gw-ping { position: absolute; z-index: 2; width: 9px; height: 9px;
    border-radius: 50%; background: #ff70cb; box-shadow: 0 0 16px #ff70cb; }
.gw-ping.p1 { top: 42px; left: 113px; }
.gw-ping.p2 { bottom: 57px; right: 41px; }
.gw-ping.p3 { bottom: 74px; left: 35px; }
.gw-kicker { color: #8da1b2; font-size: 11px; text-transform: uppercase;
    letter-spacing: .16em; font-weight: 800; margin: 20px 0 10px; }
.gw-section-title { color: #f7fafc; font-size: 25px; font-weight: 750;
    letter-spacing: -.025em; margin: 0 0 18px; }
.gw-metric { background: #0d141e; border: 1px solid rgba(255,255,255,.08);
    border-radius: 16px; padding: 20px 22px; min-height: 126px;
    box-shadow: inset 0 1px rgba(255,255,255,.025); }
.gw-metric-label { color: #93a1b2; font-size: 12px; font-weight: 700; }
.gw-metric-value { color: #f8fafc; font-size: 33px; font-weight: 800;
    line-height: 1.1; margin: 9px 0 3px; }
.gw-metric-detail { color: #5ee5d3; font-size: 11px; }
.gw-panel { background: #0d141e; border: 1px solid rgba(255,255,255,.09);
    border-radius: 20px; padding: 22px; }
.gw-panel-header { display: flex; justify-content: space-between; align-items: center;
    gap: 12px; margin-bottom: 18px; }
.gw-panel-title { color: #f4f8fb; font-size: 18px; font-weight: 750; }
.gw-chip { border: 1px solid rgba(99,227,208,.22); color: #6debd7;
    background: rgba(40,172,149,.09); border-radius: 30px; padding: 5px 9px;
    font-size: 10px; font-weight: 800; letter-spacing: .04em; white-space: nowrap; }
.gw-map-preview { position: relative; overflow: hidden; min-height: 388px;
    border-radius: 14px; border: 1px solid rgba(145,166,182,.13);
    background:
      radial-gradient(circle at 75% 27%, rgba(255,91,189,.13), transparent 25%),
      radial-gradient(circle at 31% 62%, rgba(30,214,185,.12), transparent 32%),
      linear-gradient(150deg, #101f2b, #0b1722 70%); }
.gw-map-preview::before { content: ""; position: absolute; inset: 0;
    background-image: linear-gradient(rgba(124,164,178,.055) 1px, transparent 1px),
      linear-gradient(90deg, rgba(124,164,178,.055) 1px, transparent 1px);
    background-size: 32px 32px; }
.gw-map-lines { position: absolute; inset: 0; width: 100%; height: 100%; }
.gw-preview-overlay { position: absolute; left: 24px; right: 24px; bottom: 24px;
    border: 1px solid rgba(255,255,255,.12); background: rgba(7,14,23,.88);
    backdrop-filter: blur(12px); border-radius: 13px; padding: 16px 18px; }
.gw-preview-overlay strong { display: block; color: #fff; font-size: 15px; }
.gw-preview-overlay span { display: block; color: #9eafbe; font-size: 12px;
    line-height: 1.5; margin-top: 4px; }
.gw-step { display: flex; gap: 13px; padding: 16px 0;
    border-bottom: 1px solid rgba(255,255,255,.075); }
.gw-step:last-child { border-bottom: none; }
.gw-step-n { min-width: 30px; height: 30px; display: grid; place-items: center;
    border-radius: 9px; color: #67edda; border: 1px solid rgba(103,237,218,.22);
    font-size: 11px; font-weight: 800; }
.gw-step strong { color: #eaf1f7; font-size: 13px; }
.gw-step p { color: #92a2b0; font-size: 12px; line-height: 1.5;
    margin: 4px 0 0; }
.gw-empty { border: 1px dashed rgba(123,159,176,.25);
    border-radius: 18px; background: rgba(13,24,35,.68);
    padding: 38px; min-height: 210px; }
.gw-empty-icon { width: 46px; height: 46px; display: grid; place-items: center;
    border-radius: 13px; background: rgba(90,226,205,.1); color: #74e8d8;
    font-size: 22px; margin-bottom: 14px; }
.gw-empty h3 { color: #f5f8fb; font-size: 20px; margin: 0 0 8px; }
.gw-empty p { color: #9eafbd; margin: 0; max-width: 620px; line-height: 1.6; }
.gw-status-row { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 18px; }
.gw-status-row span { padding: 7px 12px; border-radius: 30px;
    border: 1px solid rgba(255,255,255,.1); font-size: 11px; }
.gw-status-row .ok { color: #70e0a7; }
.gw-status-row .bad { color: #ff818c; }
.gw-status-row .pending { color: #b7c2cf; }
.gw-footer { color: #6e8191; font-size: 11px; padding: 24px 0 0;
    text-align: center; }
@media (max-width: 900px) {
  .gw-hero { grid-template-columns: 1fr; padding: 30px 26px; }
  .gw-radar { display: none; }
  .gw-hero h1 { font-size: 38px; }
}
</style>
"""


def _metric(label: str, detail: str) -> None:
    st.markdown(
        f'<div class="gw-metric"><div class="gw-metric-label">{label}</div>'
        '<div class="gw-metric-value">—</div>'
        f'<div class="gw-metric-detail">{detail}</div></div>',
        unsafe_allow_html=True,
    )


def render_gateways() -> None:
    """Render the new navigation destination without changing the assistant state."""
    st.markdown(GATEWAYS_STYLES, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="gw-hero">
          <div>
            <div class="gw-eyebrow">Espacio de trabajo · Gateways</div>
            <h1>La cobertura empieza<br>con un <span>buen mapa.</span></h1>
            <p>Un lugar para reunir fincas, gateways, recorridos de campo y
            resultados LoRaWAN. La primera vista está lista para conectar las
            fuentes del proyecto.</p>
            <div class="gw-hero-tags">
              <span>FINCAS</span><span>GATEWAYS</span><span>RUTAS</span><span>UPLINKS</span>
            </div>
          </div>
          <div class="gw-radar" aria-hidden="true">
            <div class="gw-ring r1"></div><div class="gw-ring r2"></div>
            <div class="gw-ring r3"></div><div class="gw-core"></div>
            <div class="gw-ping p1"></div><div class="gw-ping p2"></div>
            <div class="gw-ping p3"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="gw-kicker">Vista general</div>', unsafe_allow_html=True)
    metrics = st.columns(4, gap="small")
    with metrics[0]:
        _metric("Fincas", "Pendiente de conectar")
    with metrics[1]:
        _metric("Gateways", "Pendiente de conectar")
    with metrics[2]:
        _metric("Recorridos", "Pendiente de conectar")
    with metrics[3]:
        _metric("Uplinks", "Pendiente de conectar")

    st.markdown('<div class="gw-kicker">Área de operación</div>', unsafe_allow_html=True)
    st.markdown('<div class="gw-section-title">Todo el trabajo en una vista</div>', unsafe_allow_html=True)

    map_tab, routes_tab, results_tab = st.tabs(["◉ Mapa", "↗ Recorridos", "▥ Resultados"])
    with map_tab:
        map_column, steps_column = st.columns([1.75, 1], gap="medium")
        with map_column:
            st.markdown(
                """
                <div class="gw-panel">
                  <div class="gw-panel-header">
                    <div class="gw-panel-title">Mapa operativo</div>
                    <div class="gw-chip">VISTA CONCEPTUAL</div>
                  </div>
                  <div class="gw-map-preview">
                    <svg class="gw-map-lines" viewBox="0 0 800 390" preserveAspectRatio="none"
                         aria-hidden="true">
                      <path d="M-10 275 C110 190 165 225 270 105 S465 135 550 85 S680 175 820 48"
                        fill="none" stroke="#284356" stroke-width="18" opacity=".65"/>
                      <path d="M-10 275 C110 190 165 225 270 105 S465 135 550 85 S680 175 820 48"
                        fill="none" stroke="#41677a" stroke-width="2" stroke-dasharray="8 8" opacity=".7"/>
                      <path d="M-20 365 C145 303 270 340 340 240 S470 185 570 255 S700 305 815 220"
                        fill="none" stroke="#1c4650" stroke-width="3" opacity=".8"/>
                      <circle cx="275" cy="112" r="44" fill="none" stroke="#58e5d2"
                        stroke-width="1.5" opacity=".25"/>
                      <circle cx="275" cy="112" r="75" fill="none" stroke="#58e5d2"
                        stroke-width="1.5" opacity=".15"/>
                      <circle cx="275" cy="112" r="7" fill="#66f0dc"/>
                      <circle cx="525" cy="246" r="6" fill="#ff72c9"/>
                      <circle cx="634" cy="145" r="6" fill="#ff72c9"/>
                    </svg>
                    <div class="gw-preview-overlay">
                      <strong>Tu mapa estará aquí</strong>
                      <span>Fincas, gateways y puntos de medición aparecerán cuando
                      conectemos los datos geográficos del proyecto.</span>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with steps_column:
            st.markdown(
                """
                <div class="gw-panel">
                  <div class="gw-panel-header">
                    <div class="gw-panel-title">Flujo de trabajo</div>
                    <div class="gw-chip">3 ETAPAS</div>
                  </div>
                  <div class="gw-step"><div class="gw-step-n">01</div><div>
                    <strong>Ubicar la red</strong>
                    <p>Mostrar fincas, puntos de referencia y gateways candidatos.</p>
                  </div></div>
                  <div class="gw-step"><div class="gw-step-n">02</div><div>
                    <strong>Recorrer y medir</strong>
                    <p>Ver las rutas y pruebas capturadas con QField.</p>
                  </div></div>
                  <div class="gw-step"><div class="gw-step-n">03</div><div>
                    <strong>Validar uplinks</strong>
                    <p>Comparar los puntos con el archivo exportado del servidor.</p>
                  </div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with routes_tab:
        st.markdown(
            """
            <div class="gw-empty">
              <div class="gw-empty-icon">↗</div>
              <h3>Recorridos de campo</h3>
              <p>Aquí se verán las rutas por finca y campaña, con puntos numerados
              en el orden de la prueba. La vista se completará al conectar el
              proyecto geográfico.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with results_tab:
        st.markdown(
            """
            <div class="gw-empty">
              <div class="gw-empty-icon">▥</div>
              <h3>Resultados de cobertura</h3>
              <p>Los puntos mostrarán su estado después de compararlos con los
              uplinks del servidor. También podremos consultar RSSI, SNR y el
              gateway receptor cuando esos datos estén disponibles.</p>
              <div class="gw-status-row"><span class="ok">● Confirmado</span>
                <span class="bad">● No recibido</span>
                <span class="pending">● Pendiente</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="gw-footer">Elite Flower · Gateways · Interfaz inicial sin datos corporativos publicados</div>',
        unsafe_allow_html=True,
    )
