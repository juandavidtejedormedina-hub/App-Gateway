"""Componente MapLibre bidireccional para Streamlit 1.57+."""

from __future__ import annotations

import streamlit as st


MAP_HTML = """
<div class="gw-map-frame">
  <div class="gw-map-canvas" role="application" aria-label="Mapa interactivo de gateways"></div>
  <div class="gw-map-tools" aria-label="Herramientas del mapa">
    <button type="button" data-action="explore" class="active">Explorar</button>
    <button type="button" data-action="point">+ Punto</button>
    <button type="button" data-action="route">↗ Ruta</button>
    <button type="button" data-action="finish" hidden>Terminar</button>
    <button type="button" data-action="cancel" hidden>Cancelar</button>
    <button type="button" data-action="fit">Enfocar</button>
  </div>
  <div class="gw-map-hint">Haz clic en un punto para ver sus detalles.</div>
  <div class="gw-map-error" hidden></div>
</div>
"""

MAP_CSS = """
@import url('https://unpkg.com/maplibre-gl@6.11.2/dist/maplibre-gl.css');
.gw-map-frame { position:relative; width:100%; height:650px; min-height:440px;
  overflow:hidden; border-radius:18px; background:#0c1722; color:#e8f5f7;
  border:1px solid rgba(170,218,226,.2); box-shadow:0 18px 54px rgba(0,0,0,.23); }
.gw-map-canvas { position:absolute; inset:0; }
.gw-map-tools { position:absolute; z-index:10; top:18px; left:18px; display:flex;
  flex-wrap:wrap; gap:6px; max-width:calc(100% - 95px); padding:6px;
  border:1px solid rgba(255,255,255,.14); border-radius:13px;
  background:rgba(8,20,30,.90); backdrop-filter:blur(16px); }
.gw-map-tools button { border:0; border-radius:8px; padding:8px 11px;
  background:transparent; color:#b7cbd2; cursor:pointer; font:600 12px system-ui; }
.gw-map-tools button:hover { color:#fff; background:rgba(255,255,255,.10); }
.gw-map-tools button.active { color:#052b2b; background:#69e8d4; }
.gw-map-tools button[hidden] { display:none; }
.gw-map-hint { position:absolute; z-index:8; left:18px; bottom:22px;
  padding:9px 12px; background:rgba(8,20,30,.85); border-radius:9px;
  color:#d6e8eb; font:500 11px system-ui; pointer-events:none; }
.gw-map-error { position:absolute; z-index:20; inset:0; display:grid; place-items:center;
  padding:30px; text-align:center; background:#0c1722; color:#fbb8c0;
  font:600 14px system-ui; }
.gw-map-error[hidden] { display:none; }
.gw-pin { position:relative; display:grid; place-items:center; border:2px solid #091822;
  color:#071720; cursor:pointer; font:800 11px system-ui; line-height:1;
  box-shadow:0 3px 15px rgba(0,0,0,.4); transition:filter .16s ease; }
.gw-pin:hover { filter:brightness(1.23); z-index:4; }
.gw-pin.gateway { width:27px; height:27px; background:var(--zone-color,#ff6ac6);
  border-radius:7px; color:#071720; font-size:13px; }
.gw-pin.finca { width:17px; height:17px; border-radius:50%; background:var(--zone-color,#ffd66d); }
.gw-pin.referencia_punto { width:14px; height:14px; border-radius:50%;
  border:2px solid var(--zone-color,#a8b8c5); background:#142431; }
.gw-pin.medicion { width:25px; height:25px; border-radius:50%; background:#9daab4; }
.gw-pin.medicion.confirmado { background:#5ee2a5; }
.gw-pin.medicion.no_recibido { background:#ff7484; }
.gw-pin.medicion.pendiente { background:#b2bfcb; }
.gw-map-frame .maplibregl-popup-content { background:#0e1c28; color:#e8f5f7;
  border:1px solid rgba(255,255,255,.15); border-radius:12px; padding:14px 16px;
  box-shadow:0 14px 38px rgba(0,0,0,.33); font:12px system-ui; min-width:165px; }
.gw-map-frame .maplibregl-popup-tip { border-top-color:#0e1c28; }
.gw-map-frame .maplibregl-popup-close-button { color:#d7e6e9; font-size:18px; }
.gw-popup-title { font-size:14px; font-weight:800; padding-right:17px; }
.gw-popup-sub { color:#91aebb; margin-top:5px; }
.gw-map-frame .maplibregl-ctrl-group { border-radius:10px; overflow:hidden;
  background:rgba(9,23,33,.92); }
.gw-map-frame .maplibregl-ctrl-group button { filter:invert(1); }
.gw-map-frame .maplibregl-ctrl-attrib { background:rgba(255,255,255,.88); }
@media (max-width:680px) { .gw-map-frame { height:560px; }
  .gw-map-tools { left:10px; top:10px; max-width:calc(100% - 68px); }
  .gw-map-tools button { padding:7px 8px; font-size:11px; }
  .gw-map-hint { left:10px; bottom:20px; } }
"""

MAP_JS = """
const LIB_URL = 'https://unpkg.com/maplibre-gl@6.11.2/dist/maplibre-gl.mjs';
const mapInstances = new WeakMap();

function getLibrary() {
  if (!globalThis.__gatewayMapLibrePromise)
    globalThis.__gatewayMapLibrePromise = import(LIB_URL).catch(() => {
      globalThis.__gatewayMapLibrePromise = null;
      throw new Error('No se pudo descargar MapLibre');
    });
  return globalThis.__gatewayMapLibrePromise;
}

function style() {
  return {
    version: 8,
    sources: { osm: { type: 'raster', tileSize: 256,
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      attribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap contributors</a>' } },
    layers: [
      { id:'background', type:'background', paint:{'background-color':'#0d1b27'} },
      { id:'base', type:'raster', source:'osm', paint:{'raster-fade-duration':100} }
    ]
  };
}

function visible(feature, layers) {
  const kind = feature?.properties?.kind;
  return kind === 'gateway' ? layers.gateways
    : kind === 'finca' ? layers.fincas
    : kind === 'referencia_punto' ? layers.referencias
    : kind === 'medicion' ? layers.mediciones
    : kind === 'recorrido' || kind === 'referencia' ? layers.recorridos : true;
}

function popupNode(feature) {
  const box = document.createElement('div');
  const title = document.createElement('div');
  title.className = 'gw-popup-title';
  title.textContent = String(feature.properties?.name || 'Sin nombre');
  const sub = document.createElement('div');
  sub.className = 'gw-popup-sub';
  const status = feature.properties?.status;
  sub.textContent = [feature.properties?.region,
    feature.properties?.roster_name ? `Excel: ${feature.properties.roster_name}` : '',
    status ? status.replaceAll('_',' ') : ''].filter(Boolean).join(' · ');
  box.append(title, sub);
  return box;
}

function fitToFeatures(instance) {
  const bounds = new instance.lib.LngLatBounds();
  for (const feature of instance.features) {
    const geometry = feature.geometry || {};
    const points = geometry.type === 'Point' ? [geometry.coordinates]
      : geometry.type === 'LineString' ? geometry.coordinates : [];
    for (const coord of points) if (Array.isArray(coord) && coord.length >= 2) bounds.extend(coord);
  }
  if (!bounds.isEmpty()) instance.map.fitBounds(bounds, { padding:70, maxZoom:12, duration:800 });
}

function updateDraft(instance) {
  if (!instance.loaded) return;
  const source = instance.map.getSource('draft');
  source.setData({type:'FeatureCollection',features:instance.draft.length > 1 ? [{
    type:'Feature',properties:{},geometry:{type:'LineString',coordinates:instance.draft}
  }] : []});
  instance.hint.textContent = instance.mode === 'route'
    ? `${instance.draft.length} vértices · Terminar para guardar la ruta`
    : instance.mode === 'point' ? 'Haz clic en el mapa para agregar un punto.'
    : 'Haz clic en un punto para ver sus detalles.';
}

function finishRoute(instance) {
  if (instance.draft.length < 2) return;
  const feature = {type:'Feature',geometry:{type:'LineString',coordinates:[...instance.draft]},
    properties:{kind:'recorrido',name:'Ruta dibujada',region:'Dibujo local',id:crypto.randomUUID()}};
  instance.draft = [];
  instance.setTriggerValue('drawn_feature', feature);
  updateDraft(instance);
}

function setMode(instance, mode) {
  instance.mode = mode;
  if (mode !== 'route') instance.draft = [];
  instance.root.querySelectorAll('[data-action]').forEach(button => {
    button.classList.toggle('active',button.dataset.action === mode);
    if (button.dataset.action === 'finish' || button.dataset.action === 'cancel')
      button.hidden = mode !== 'route';
  });
  instance.map.getCanvas().style.cursor = mode === 'explore' ? '' : 'crosshair';
  updateDraft(instance);
}

function drawMarkers(instance) {
  if (instance.popup) {instance.popup.remove();instance.popup = null;}
  instance.markers.forEach(marker => marker.remove());
  instance.markers = [];
  for (const feature of instance.features) {
    const geometry = feature.geometry || {};
    if (geometry.type !== 'Point') continue;
    const props = feature.properties || {};
    const el = document.createElement('button');
    el.type = 'button';
    el.className = ['gw-pin',props.kind,props.status].filter(Boolean).join(' ');
    if (props.zone_color) el.style.setProperty('--zone-color', String(props.zone_color));
    el.textContent = props.kind === 'gateway' ? 'G'
      : props.kind === 'medicion' ? String(props.number || '') : '';
    el.title = String(props.name || 'Punto');
    el.setAttribute('aria-label',el.title);
    const marker = new instance.lib.Marker({element:el,anchor:'bottom'})
      .setLngLat(geometry.coordinates).addTo(instance.map);
    el.addEventListener('click',event => {
      event.stopPropagation();
      if (instance.popup) instance.popup.remove();
      instance.popup = new instance.lib.Popup({offset:22}).setLngLat(geometry.coordinates)
        .setDOMContent(popupNode(feature)).addTo(instance.map);
    });
    instance.markers.push(marker);
  }
}

function applyData(instance, data) {
  instance.data = data;
  if (!instance.loaded) return;
  const all = Array.isArray(data.features) ? data.features : [];
  instance.features = all.filter(feature => visible(feature, data.layers || {}));
  const lines = instance.features.filter(feature => feature.geometry?.type === 'LineString');
  instance.map.getSource('routes').setData({type:'FeatureCollection',features:lines});
  drawMarkers(instance);
  const dark = data.basemap === 'Oscuro';
  instance.map.setPaintProperty('base','raster-brightness-max',dark ? 0.50 : 1);
  instance.map.setPaintProperty('base','raster-saturation',dark ? -0.65 : 0);
  instance.map.setPaintProperty('base','raster-contrast',dark ? 0.15 : 0);
  if (instance.fitKey !== data.fit_key) {
    instance.fitKey = data.fit_key;
    fitToFeatures(instance);
  }
}

export default function(component) {
  const {parentElement, data, setTriggerValue} = component;
  const root = parentElement.querySelector('.gw-map-frame');
  let instance = mapInstances.get(root);
  if (instance) {
    instance.setTriggerValue = setTriggerValue;
    applyData(instance, data);
    return;
  }
  instance = {root, data, loaded:false, mode:'explore', draft:[], markers:[],
    features:[], popup:null, fitKey:null, hint:root.querySelector('.gw-map-hint'),
    setTriggerValue, disposed:false};
  mapInstances.set(root,instance);
  getLibrary().then(lib => {
    if (instance.disposed) return;
    instance.lib = lib;
    instance.map = new lib.Map({container:root.querySelector('.gw-map-canvas'),style:style(),
      center:[-74.08,4.64],zoom:11,attributionControl:false,maxZoom:19});
    instance.map.addControl(new lib.NavigationControl({visualizePitch:true}),'top-right');
    instance.map.addControl(new lib.AttributionControl({compact:true}),'bottom-right');
    instance.map.doubleClickZoom.disable();
    instance.map.on('load',() => {
      instance.map.addSource('routes',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
      instance.map.addLayer({id:'reference-lines',type:'line',source:'routes',
        filter:['==',['get','kind'],'referencia'],
        paint:{'line-color':['coalesce',['get','zone_color'],'#f5a9d7'],
          'line-width':2,'line-dasharray':[2,2],'line-opacity':0.78}});
      instance.map.addLayer({id:'route-lines',type:'line',source:'routes',
        filter:['!=',['get','kind'],'referencia'],
        layout:{'line-cap':'round','line-join':'round'},
        paint:{'line-color':['coalesce',['get','zone_color'],'#59e6d5'],
          'line-width':4,'line-opacity':0.9}});
      instance.map.addSource('draft',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
      instance.map.addLayer({id:'draft-line',type:'line',source:'draft',
        paint:{'line-color':'#ffe28a','line-width':3,'line-dasharray':[2,2]}});
      instance.loaded = true;
      applyData(instance,instance.data);
    });
    instance.map.on('click',event => {
      if (instance.mode === 'point') {
        const feature = {type:'Feature',geometry:{type:'Point',coordinates:[event.lngLat.lng,event.lngLat.lat]},
          properties:{kind:'medicion',name:'Punto dibujado',region:'Dibujo local',status:'pendiente',id:crypto.randomUUID()}};
        instance.setTriggerValue('drawn_feature',feature);
      } else if (instance.mode === 'route') {
        instance.draft.push([event.lngLat.lng,event.lngLat.lat]);
        updateDraft(instance);
      }
    });
    instance.map.on('dblclick',event => {
      if (instance.mode === 'route') {event.preventDefault();finishRoute(instance);setMode(instance,'explore');}
    });
    root.querySelectorAll('[data-action]').forEach(button => button.onclick = () => {
      const action = button.dataset.action;
      if (action === 'fit') fitToFeatures(instance);
      else if (action === 'finish') {finishRoute(instance);setMode(instance,'explore');}
      else if (action === 'cancel') setMode(instance,'explore');
      else setMode(instance,action);
    });
  }).catch(error => {
    const box = root.querySelector('.gw-map-error');
    box.hidden = false;
    box.textContent = error.message || 'No se pudo cargar el mapa';
  });
  return () => {
    instance.disposed = true;
    if (instance.popup) instance.popup.remove();
    instance.markers.forEach(marker => marker.remove());
    if (instance.map) instance.map.remove();
    mapInstances.delete(root);
  };
}
"""


_MAP = st.components.v2.component(
    "gateway_maplibre",
    html=MAP_HTML,
    css=MAP_CSS,
    js=MAP_JS,
)


def gateway_map(*, features: list[dict], layers: dict[str, bool], basemap: str,
                fit_key: str, key: str = "gateway_map"):
    """Muestra el mapa y devuelve los eventos de selección y trazado."""
    return _MAP(
        data={"features": features, "layers": layers, "basemap": basemap, "fit_key": fit_key},
        key=key,
        height=650,
        width="stretch",
        on_drawn_feature_change=lambda: None,
    )
