"""Espacio interactivo de Gateways dentro del asistente."""

from __future__ import annotations

import json
import os
from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st

from gateway_data import REGIONS, counts, feature_collection, load_private_kmz
from gateway_map_component import gateway_map
from gateway_roster import ZONE_COLORS, load_roster, reconcile_features


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
.gw-map-side.private .gw-dot.gateway { border-radius:3px; background:#d4e6ec; }
.gw-map-side.private .gw-dot.finca { background:#d4e6ec; }
.gw-callout { border-left:2px solid #62decf; padding-left:12px; margin-top:18px;
  color:#91aebb; font-size:11px; line-height:1.6; }
.gw-zone-list { display:grid; gap:7px; margin:15px 0; max-height:400px; overflow:auto; }
.gw-zone-row { display:flex; gap:9px; align-items:flex-start; border:1px solid rgba(255,255,255,.07);
  border-radius:10px; padding:8px 9px; background:rgba(255,255,255,.025); }
.gw-zone-row.selected { border-color:rgba(122,239,216,.42); background:rgba(89,230,213,.09); }
.gw-zone-swatch { flex:none; width:9px; height:9px; margin-top:4px; border-radius:50%;
  background:var(--zone-color); box-shadow:0 0 0 3px rgba(255,255,255,.05); }
.gw-zone-row strong { display:block; color:#e8f5f6; font-size:12px; }
.gw-zone-row small { display:block; color:#9eb8c2; font-size:10px; margin-top:2px; }
.gw-dot.reference { border:2px solid #a8b8c5; background:#142431; }
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


@st.cache_data(max_entries=3, show_spinner=False)
def _private_roster(path: str, modified: float) -> list[dict]:
    del modified
    return load_roster(path)


def _source_data() -> tuple[list[dict], list[dict], bool, str | None]:
    kmz_setting = os.getenv("GATEWAYS_KMZ_PATH", "").strip()
    xlsx_setting = os.getenv("GATEWAYS_XLSX_PATH", "").strip()
    if not kmz_setting:
        warning = "Falta configurar GATEWAYS_KMZ_PATH." if xlsx_setting else None
        return [], [], False, warning
    try:
        kmz_path = Path(kmz_setting).expanduser().resolve(strict=True)
        features = _private_features(str(kmz_path), kmz_path.stat().st_mtime)
    except (FileNotFoundError, OSError, ValueError):
        return [], [], False, "No se pudo leer el KMZ local."
    if not xlsx_setting:
        return features, [], True, "No se configuró GATEWAYS_XLSX_PATH; se muestran solo los puntos del KMZ."
    try:
        xlsx_path = Path(xlsx_setting).expanduser().resolve(strict=True)
        roster = _private_roster(str(xlsx_path), xlsx_path.stat().st_mtime)
        mapped_features, matched_roster = reconcile_features(features, roster)
        return mapped_features, matched_roster, True, None
    except (FileNotFoundError, OSError, ValueError):
        return features, [], True, "No se pudo leer la hoja Detallado; se muestran solo los puntos del KMZ."


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


def _zone_panel(features: list[dict], roster: list[dict], selected_zone: str) -> str:
    rows = []
    for zone in REGIONS:
        members = [item for item in roster if item["zone"] == zone]
        if not members:
            continue
        gateways = sum(item["properties"].get("kind") == "gateway"
                       and item["properties"].get("region") == zone for item in features)
        located = sum(item["on_map"] for item in members)
        selected_class = " selected" if selected_zone == zone else ""
        color = ZONE_COLORS[zone]
        rows.append(
            f'<div class="gw-zone-row{selected_class}">'
            f'<i class="gw-zone-swatch" style="--zone-color:{color}"></i><div>'
            f'<strong>{escape(zone)}</strong><small>{len(members)} fincas · '
            f'{located} con punto homónimo · {gateways} candidatos</small></div></div>'
        )
    return (
        '<div class="gw-map-side private"><h3>Zonas del proyecto</h3>'
        '<p>En el orden de la hoja Detallado. Los colores siguen las carpetas del KMZ.</p>'
        f'<div class="gw-zone-list">{"".join(rows)}</div>'
        '<div class="gw-legend"><span><i class="gw-dot gateway"></i>Cuadrado: gateway candidato</span>'
        '<span><i class="gw-dot finca"></i>Círculo: finca del Excel</span>'
        '<span><i class="gw-dot reference"></i>Otro punto del KMZ</span></div>'
        '<div class="gw-callout">Las fincas sin punto homónimo siguen en el listado, '
        'pero no se colocan en una ubicación inventada.</div></div>'
    )


def render_gateways() -> None:
    """Mapa interactivo. Los datos de empresa no se incluyen en GitHub."""
    st.markdown(GATEWAYS_STYLES, unsafe_allow_html=True)
    source, roster, is_private, source_error = _source_data()
    if "gateway_drawings" not in st.session_state:
        st.session_state.gateway_drawings = []

    badge_class = "" if is_private else " demo"
    if roster:
        badge = "KMZ y Excel locales"
        headline = "Tus zonas. <span>Tus fincas y gateways.</span>"
        description = ("Fincas del listado, gateways y trazos de Google Earth organizados por zona. "
                       "Filtra, inspecciona puntos y dibuja nuevas rutas.")
    elif is_private:
        badge = "KMZ local privado"
        headline = "Explora la red. <span>Planea la cobertura.</span>"
        description = ("Fincas, gateways, recorridos y pruebas reunidos en un mapa dinámico. "
                       "Filtra por región, inspecciona puntos y dibuja nuevas rutas.")
    else:
        badge = "Sin datos cargados"
        headline = "Mapa privado. <span>Sin puntos de muestra.</span>"
        description = ("Esta página pública no carga ubicaciones de la empresa. Abre el proyecto "
                       "en el entorno privado para ver el KMZ y el Excel reales.")
    st.markdown(
        '<div class="gw-heading"><div class="gw-eyebrow">Centro de operaciones · LoRaWAN</div>'
        f'<h1>{headline}</h1>'
        f'<p>{description}</p>'
        f'<div class="gw-intro-row"><span class="gw-badge{badge_class}">{badge}</span>'
        '<span class="gw-note">Mapa base OpenStreetMap · requiere internet</span></div></div>',
        unsafe_allow_html=True,
    )
    if source_error:
        st.warning(source_error)
    if not is_private:
        st.info("No hay fincas, gateways ni mediciones en esta vista pública. "
                "Se retiraron los puntos ficticios para no confundirlos con datos de campo. "
                "Los archivos reales solo se leen en una ejecución privada autorizada.")
        return

    available_regions = {str(item["properties"].get("region") or "Sin región") for item in source}
    available_regions.update(item["zone"] for item in roster)
    region_names = [zone for zone in REGIONS if zone in available_regions]
    region_names.extend(sorted(available_regions - set(region_names)))
    controls = st.columns([1.35, 1.15, 2.3], gap="small", vertical_alignment="bottom")
    with controls[0]:
        region = st.selectbox("Zona", ["Todas", *region_names], key="gw_region")
    with controls[1]:
        basemap = st.segmented_control("Estilo", ["Claro", "Oscuro"], default="Oscuro", key="gw_basemap")
    with controls[2]:
        layer_options = (["Gateways", "Fincas", "Otros puntos", "Mediciones", "Trazados"]
                         if roster else ["Gateways", "Fincas", "Mediciones", "Trazados"])
        visible_labels = st.pills(
            "Capas visibles", layer_options, default=layer_options,
            selection_mode="multi", key="gw_layers", wrap=True,
        )
    selected = [item for item in source if region == "Todas" or item["properties"].get("region") == region]
    selected_roster = [item for item in roster if region == "Todas" or item["zone"] == region]
    drawings = st.session_state.gateway_drawings
    visible_features = selected + (drawings if region == "Todas" else [])
    item_counts = counts(visible_features)

    metrics = st.columns(4, gap="small")
    if roster:
        metrics[0].metric("Zonas", len({item["zone"] for item in selected_roster}))
        metrics[1].metric("Fincas del Excel", len(selected_roster))
        metrics[2].metric("Gateways candidatos", item_counts["gateway"])
        metrics[3].metric("Fincas con punto", sum(item["on_map"] for item in selected_roster))
    else:
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
                    "referencias": "Otros puntos" in visible_labels,
                    "mediciones": "Mediciones" in visible_labels, "recorridos": "Trazados" in visible_labels},
            basemap=basemap or "Oscuro",
            fit_key=f"{region}:{is_private}",
        )
    with info_column:
        if roster:
            st.markdown(_zone_panel(source, roster, region), unsafe_allow_html=True)
        else:
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

    if roster:
        with st.expander("Fincas por zona · hoja Detallado", expanded=region != "Todas"):
            if selected_roster:
                table = pd.DataFrame([
                    {"Orden": row["zone_order"], "Zona": row["zone"],
                     "Finca": row["name"],
                     "En mapa": "Sí" if row["on_map"] else "Sin punto homónimo"}
                    for row in selected_roster
                ])
                st.dataframe(table, hide_index=True, width="stretch", height=330,
                             alt="Fincas del Excel ordenadas por zona y coincidencia con el KMZ")
            else:
                st.caption("Esta carpeta del KMZ no contiene fincas en la hoja Detallado.")
            st.caption("Las coincidencias usan el nombre normalizado dentro de la misma zona; "
                       "los nombres genéricos o diferentes quedan pendientes de revisión.")

    drawn = _safe_drawn_feature(getattr(result, "drawn_feature", None))
    if drawn and len(st.session_state.gateway_drawings) < 500:
        known_ids = {item["properties"].get("id") for item in st.session_state.gateway_drawings}
        if drawn["properties"]["id"] not in known_ids:
            st.session_state.gateway_drawings.append(drawn)
            st.rerun()

    st.caption(
        "Los datos reales solo se leen en un entorno privado desde GATEWAYS_KMZ_PATH y "
        "GATEWAYS_XLSX_PATH. La vista pública no muestra ubicaciones. "
        "El mapa web requiere internet; la captura offline continúa en QField."
    )


if __name__ == "__main__":
    st.set_page_config(page_title="Gateways · Elite Flower", layout="wide")
    render_gateways()
