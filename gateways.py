"""Espacio interactivo de Gateways dentro del asistente."""

from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from gateway_data import counts, demo_features, feature_collection, load_private_kmz
from gateway_map_component import gateway_map


GATEWAYS_STYLES = """
<style>
.gw-heading { position:relative; overflow:hidden; padding:30px 36px; margin:18px 0 25px;
  border:1px solid rgba(143,221,218,.15); border-radius:24px;
  background:radial-gradient(circle at 88% 15%,rgba(255,91,190,.18),transparent 30%),
    radial-gradient(circle at 65% 110%,rgba(65,228,205,.10),transparent 36%),
    linear-gradient(115deg,#102333,#0a1521 72%); }
.gw-heading::after { content:''; position:absolute; width:230px; height:230px; right:7%; top:-115px;
  border:1px solid rgba(90,234,216,.20); border-radius:50%;
  box-shadow:0 0 0 38px rgba(90,234,216,.035),0 0 0 80px rgba(90,234,216,.025); }
.gw-eyebrow { color:#70e9d7; font-size:11px; font-weight:800; letter-spacing:.17em;
  text-transform:uppercase; margin-bottom:10px; }
.gw-heading h1 { color:#f7fbfd; font-size:clamp(31px,4vw,50px); letter-spacing:-.04em;
  line-height:1.1; margin:0 0 10px; }
.gw-heading h1 span { color:#ff79ce; }
.gw-heading p { color:#a9bfcb; font-size:14px; max-width:730px; line-height:1.6; margin:0; }
.gw-intro-row { display:flex; flex-wrap:wrap; align-items:center; gap:10px; margin-top:17px; }
.gw-badge { padding:6px 10px; border-radius:40px; font:800 10px system-ui;
  color:#76eddb; border:1px solid rgba(118,237,219,.29); background:rgba(69,209,187,.08); }
.gw-badge.demo { color:#ffd892; border-color:rgba(255,216,146,.34);
  background:rgba(255,216,146,.07); }
.gw-note { color:#879fac; font-size:11px; }
.gw-section-title { color:#edf7f9; font-weight:760; font-size:18px; margin:5px 0 12px; }
.gw-map-side { border:1px solid rgba(255,255,255,.10); border-radius:17px;
  background:#101e2a; padding:20px; min-height:190px; }
.gw-map-side h3 { color:#f2fafb; font-size:16px; margin:0 0 10px; }
.gw-map-side p { color:#a4b8c2; font-size:12px; line-height:1.6; margin:0; }
.gw-legend { display:grid; gap:9px; margin:16px 0; }
.gw-legend span { display:flex; align-items:center; gap:9px; color:#c6d8de; font-size:12px; }
.gw-dot { width:11px; height:11px; border-radius:50%; background:#a8b8c5; }
.gw-dot.ok { background:#5ee2a5; }.gw-dot.bad { background:#ff7484; }
.gw-dot.gateway { background:#ff6ac6; }.gw-dot.finca { background:#ffd66d; }
.gw-callout { border-left:2px solid #62decf; padding-left:12px; margin-top:18px;
  color:#91aebb; font-size:11px; line-height:1.6; }
[data-testid="stWidgetLabel"] p { color:#abc7cf !important; }
[data-testid="stMetric"] { padding:14px 17px; border:1px solid rgba(129,220,214,.14);
  border-radius:14px; background:rgba(15,31,42,.78); }
[data-testid="stMetricLabel"] p { color:#9dbbc4 !important; }
[data-testid="stMetricValue"] p { color:#f1fcfc !important; }
button[data-variant="pills"], button[data-variant="segmented_control"] {
  border-color:rgba(133,216,216,.3) !important; background:#122330 !important; }
button[data-variant="pills"] p, button[data-variant="segmented_control"] p {
  color:#b8d0d7 !important; }
button[data-variant="pills"][data-selected="true"],
button[data-variant="segmented_control"][data-selected="true"] {
  border-color:#6de4d4 !important; background:#164144 !important; }
button[data-variant="pills"][data-selected="true"] p,
button[data-variant="segmented_control"][data-selected="true"] p { color:#8bf5e5 !important; }
@media (max-width:700px) { .gw-heading { padding:25px 22px; } }
</style>
"""


@st.cache_data(max_entries=3, show_spinner=False)
def _private_features(path: str, modified: float) -> list[dict]:
    del modified  # La fecha de modificación invalida la caché cuando cambia el KMZ.
    return load_private_kmz(path)


def _source_features() -> tuple[list[dict], bool, str | None]:
    private_path = os.getenv("GATEWAYS_KMZ_PATH", "").strip()
    if not private_path:
        return demo_features(), False, None
    try:
        path = Path(private_path).expanduser().resolve(strict=True)
        return _private_features(str(path), path.stat().st_mtime), True, None
    except (FileNotFoundError, OSError, ValueError) as error:
        return demo_features(), False, str(error)


def _safe_drawn_feature(value: object) -> dict | None:
    if not isinstance(value, dict) or value.get("type") != "Feature":
        return None
    geometry = value.get("geometry")
    properties = value.get("properties")
    if not isinstance(geometry, dict) or not isinstance(properties, dict):
        return None
    kind = geometry.get("type")
    points = [geometry.get("coordinates")] if kind == "Point" else geometry.get("coordinates")
    if kind not in {"Point", "LineString"} or not isinstance(points, list) or len(points) > 500:
        return None
    if kind == "LineString" and len(points) < 2:
        return None
    for point in points:
        if not isinstance(point, list) or len(point) != 2:
            return None
        lon, lat = point
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            return None
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            return None
    name = str(properties.get("name") or "Trazo local")[:100]
    feature_id = str(properties.get("id") or "")[:80]
    return {
        "type": "Feature",
        "geometry": {"type": kind, "coordinates": geometry["coordinates"]},
        "properties": {"kind": "medicion" if kind == "Point" else "recorrido",
                       "name": name, "region": "Dibujo local", "status": "pendiente",
                       "id": feature_id},
    }


def render_gateways() -> None:
    """Mapa interactivo. Los datos de empresa no se incluyen en GitHub."""
    st.markdown(GATEWAYS_STYLES, unsafe_allow_html=True)
    source, is_private, source_error = _source_features()
    if "gateway_drawings" not in st.session_state:
        st.session_state.gateway_drawings = []

    badge_class = "" if is_private else " demo"
    badge = "KMZ local privado" if is_private else "Datos ficticios"
    st.markdown(
        '<div class="gw-heading"><div class="gw-eyebrow">Centro de operaciones · LoRaWAN</div>'
        '<h1>Explora la red. <span>Planea la cobertura.</span></h1>'
        '<p>Fincas, gateways, recorridos y pruebas reunidos en un mapa dinámico. '
        'Filtra por región, inspecciona puntos y dibuja nuevas rutas.</p>'
        f'<div class="gw-intro-row"><span class="gw-badge{badge_class}">{badge}</span>'
        '<span class="gw-note">Mapa base OpenStreetMap · requiere internet</span></div></div>',
        unsafe_allow_html=True,
    )
    if source_error:
        st.warning("No se pudo abrir el KMZ local; se muestran datos de demostración.")

    region_names = sorted({str(item["properties"].get("region") or "Sin región") for item in source})
    controls = st.columns([1.35, 1.15, 2.3], gap="small", vertical_alignment="bottom")
    with controls[0]:
        region = st.selectbox("Región", ["Todas", *region_names], key="gw_region")
    with controls[1]:
        basemap = st.segmented_control("Estilo", ["Claro", "Oscuro"], default="Oscuro", key="gw_basemap")
    with controls[2]:
        visible_labels = st.pills(
            "Capas visibles", ["Gateways", "Fincas", "Mediciones", "Trazados"],
            default=["Gateways", "Fincas", "Mediciones", "Trazados"],
            selection_mode="multi", key="gw_layers", wrap=True,
        )
    selected = [item for item in source if region == "Todas" or item["properties"].get("region") == region]
    drawings = st.session_state.gateway_drawings
    visible_features = selected + (drawings if region == "Todas" else [])
    item_counts = counts(visible_features)

    metrics = st.columns(4, gap="small")
    metrics[0].metric("Gateways", item_counts["gateway"])
    metrics[1].metric("Fincas / referencias", item_counts["finca"])
    metrics[2].metric("Mediciones", item_counts["medicion"])
    metrics[3].metric("Rutas y trazos", item_counts["recorrido"] + item_counts["referencia"])

    st.markdown('<div class="gw-section-title">Mapa interactivo</div>', unsafe_allow_html=True)
    map_column, info_column = st.columns([3.7, 1.15], gap="medium")
    with map_column:
        result = gateway_map(
            features=visible_features,
            layers={"gateways": "Gateways" in visible_labels, "fincas": "Fincas" in visible_labels,
                    "mediciones": "Mediciones" in visible_labels, "recorridos": "Trazados" in visible_labels},
            basemap=basemap or "Oscuro",
            fit_key=f"{region}:{is_private}",
        )
    with info_column:
        st.markdown(
            '<div class="gw-map-side"><h3>Lectura del mapa</h3>'
            '<p>Haz clic en los símbolos para ver el nombre y la región. '
            'Los números indican el orden de los puntos de prueba.</p>'
            '<div class="gw-legend"><span><i class="gw-dot gateway"></i>Gateway</span>'
            '<span><i class="gw-dot finca"></i>Finca o referencia</span>'
            '<span><i class="gw-dot ok"></i>Uplink confirmado</span>'
            '<span><i class="gw-dot bad"></i>No recibido</span>'
            '<span><i class="gw-dot"></i>Pendiente</span></div>'
            '<div class="gw-callout">Usa <b>+ Punto</b> o <b>Ruta</b> dentro del mapa. '
            'Termina la ruta con el botón o doble clic. Los trazos se mantienen '
            'en esta sesión y puedes descargarlos abajo.</div></div>',
            unsafe_allow_html=True,
        )
        st.space("small")
        if drawings:
            st.download_button(
                "Descargar mis trazos (GeoJSON)",
                data=json.dumps(feature_collection(drawings), ensure_ascii=False, indent=2),
                file_name="trazos_gateways.geojson", mime="application/geo+json",
                width="stretch", icon=":material/download:",
            )
            st.caption(f"{len(drawings)} trazo(s) de esta sesión. No se guardan en el servidor.")
        else:
            st.caption("Todavía no has dibujado puntos o rutas.")

    drawn = _safe_drawn_feature(getattr(result, "drawn_feature", None))
    if drawn and len(st.session_state.gateway_drawings) < 500:
        known_ids = {item["properties"].get("id") for item in st.session_state.gateway_drawings}
        if drawn["properties"]["id"] not in known_ids:
            st.session_state.gateway_drawings.append(drawn)
            st.rerun()

    st.caption(
        "La vista pública usa ubicaciones ficticias. Para datos de empresa, ejecuta la app en un "
        "entorno privado y configura GATEWAYS_KMZ_PATH hacia el archivo KMZ local. "
        "El mapa web necesita conexión; la captura offline continúa en QField."
    )


if __name__ == "__main__":
    st.set_page_config(page_title="Gateways · Elite Flower", layout="wide")
    render_gateways()
