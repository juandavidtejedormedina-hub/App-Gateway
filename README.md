# App Gateway

Aplicación de Elite Flower con el asistente original y un mapa interactivo de
Gateways. La navegación superior permite cambiar entre ambas vistas.

La sección Gateways usa MapLibre GL JS integrado con un componente bidireccional
de Streamlit. Permite filtrar por región, activar capas, consultar puntos y
dibujar puntos o rutas. Los trazos se conservan durante la sesión y pueden
descargarse en GeoJSON. La aplicación pública contiene **ubicaciones ficticias**:
ningún KMZ ni coordenada de la empresa se incluye en el repositorio.

Para utilizar el KMZ real, ejecuta la app **en un entorno privado** y establece
`GATEWAYS_KMZ_PATH` con la ruta absoluta del archivo antes de iniciar Streamlit.
No configures esa variable en el despliegue público. El archivo se lee localmente,
sin modificarlo ni copiarlo al repositorio.

En PowerShell, por ejemplo:

```powershell
$env:GATEWAYS_KMZ_PATH = 'C:\ruta\privada\mapa.kmz'
streamlit run app.py
```

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
