# App Gateway

Aplicación de Elite Flower con el asistente original y un mapa interactivo de
Gateways. La navegación superior permite cambiar entre ambas vistas.

La sección Gateways usa MapLibre GL JS integrado con un componente bidireccional
de Streamlit. Permite filtrar por zona, activar capas, consultar puntos y
dibujar puntos o rutas. Los trazos se conservan durante la sesión y pueden
descargarse en GeoJSON. La aplicación pública no muestra puntos de muestra ni
ubicaciones de la empresa: ningún KMZ, Excel o coordenada real se incluye en el
repositorio.

Para utilizar los datos reales, ejecuta la app **en un entorno privado** y
establece `GATEWAYS_KMZ_PATH` y `GATEWAYS_XLSX_PATH` con las rutas absolutas antes
de iniciar Streamlit. El KMZ aporta ubicaciones y carpetas; la hoja `Detallado`
del Excel aporta el listado y orden de las fincas por zona. No configures esas
variables en el despliegue público. Los archivos se leen localmente, sin
modificarlos ni copiarlos al repositorio.

En PowerShell, por ejemplo:

```powershell
$env:GATEWAYS_KMZ_PATH = 'C:\ruta\privada\mapa.kmz'
$env:GATEWAYS_XLSX_PATH = 'C:\ruta\privada\fincas.xlsx'
streamlit run app.py
```

El cruce solo acepta nombres equivalentes dentro de la misma zona (ignorando
mayúsculas, tildes y prefijos como «Finca»). Las fincas sin punto homónimo en
el KMZ aparecen en la tabla como pendientes de ubicación; no se les asigna una
coordenada aproximada. Los demás puntos del KMZ se muestran como referencias.

El mapa base usa teselas de OpenStreetMap para visualización interactiva; requiere
internet y atribución visible. Para un despliegue intensivo o mapas sin conexión,
se necesita un proveedor o servidor de teselas adecuado. La captura offline de
campo sigue haciéndose con QField.

Compatible con Streamlit Community Cloud.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Para probar únicamente la sección del mapa: `streamlit run gateways.py`.
