"""GeoJSON para el visor; el KMZ de empresa solo se lee desde una ruta local."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


REGIONS = ("Antioquia", "Cachipay", "Centro", "Norte", "Occidente", "Sur")
KML_FOLDERS = (*REGIONS, "Medicion de la linea")
KML_NS = "{http://www.opengis.net/kml/2.2}"
MAX_KMZ_BYTES = 20 * 1024 * 1024
MAX_KML_BYTES = 50 * 1024 * 1024


def _feature(kind: str, name: str, coordinates, *, region: str = "Demo", **extra):
    geometry_type = "Point" if kind in {"gateway", "finca", "medicion"} else "LineString"
    return {
        "type": "Feature",
        "geometry": {"type": geometry_type, "coordinates": coordinates},
        "properties": {"kind": kind, "name": name, "region": region, **extra},
    }


def demo_features() -> list[dict]:
    """Datos inventados para la versión pública; no corresponden a fincas reales."""
    return [
        _feature("gateway", "Gateway de muestra A", [-74.0860, 4.6245], status="candidato"),
        _feature("gateway", "Gateway de muestra B", [-74.0665, 4.6410], status="candidato"),
        _feature("finca", "Predio ficticio 01", [-74.0930, 4.6405]),
        _feature("finca", "Predio ficticio 02", [-74.0750, 4.6505]),
        _feature("finca", "Predio ficticio 03", [-74.0530, 4.6290]),
        _feature("medicion", "Prueba ficticia 1", [-74.0920, 4.6280], status="confirmado", number=1),
        _feature("medicion", "Prueba ficticia 2", [-74.0850, 4.6335], status="confirmado", number=2),
        _feature("medicion", "Prueba ficticia 3", [-74.0770, 4.6370], status="pendiente", number=3),
        _feature("medicion", "Prueba ficticia 4", [-74.0690, 4.6420], status="no_recibido", number=4),
        _feature("medicion", "Prueba ficticia 5", [-74.0610, 4.6375], status="pendiente", number=5),
        _feature("recorrido", "Recorrido de demostración", [
            [-74.0920, 4.6280], [-74.0850, 4.6335], [-74.0770, 4.6370],
            [-74.0690, 4.6420], [-74.0610, 4.6375],
        ]),
    ]


def _coordinates(text: str | None) -> list[list[float]]:
    points = []
    for item in (text or "").split():
        try:
            lon, lat = (float(value) for value in item.split(",")[:2])
        except (ValueError, TypeError):
            continue
        if -180 <= lon <= 180 and -90 <= lat <= 90:
            points.append([lon, lat])
    return points


def _name(element: ET.Element) -> str:
    return (element.findtext(f"{KML_NS}name") or "Sin nombre").strip()[:120]


def load_private_kmz(path: str | Path) -> list[dict]:
    """Convierte puntos y líneas de un KMZ local a GeoJSON, sin copiar el archivo."""
    kmz_path = Path(path).expanduser().resolve(strict=True)
    if kmz_path.suffix.lower() != ".kmz" or kmz_path.stat().st_size > MAX_KMZ_BYTES:
        raise ValueError("El archivo debe ser un KMZ de hasta 20 MB")
    try:
        with ZipFile(kmz_path) as archive:
            candidates = [item for item in archive.infolist() if item.filename.lower().endswith(".kml")]
            if not candidates or candidates[0].file_size > MAX_KML_BYTES:
                raise ValueError("El KMZ no contiene un KML válido de hasta 50 MB")
            root = ET.fromstring(archive.read(candidates[0]))
    except (BadZipFile, ET.ParseError) as error:
        raise ValueError("No se pudo leer el KMZ") from error

    features: list[dict] = []

    def walk(node: ET.Element, region: str = "Sin región") -> None:
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "Folder" and _name(node) in KML_FOLDERS:
            region = _name(node)
        if tag == "Placemark":
            name = _name(node)
            for point in node.findall(f".//{KML_NS}Point"):
                coords = _coordinates(point.findtext(f"{KML_NS}coordinates"))
                if coords:
                    kind = "gateway" if "gateway" in name.casefold() else "finca"
                    features.append(_feature(kind, name, coords[0], region=region))
            for line in node.findall(f".//{KML_NS}LineString"):
                coords = _coordinates(line.findtext(f"{KML_NS}coordinates"))
                if len(coords) >= 2:
                    features.append(_feature("referencia", name, coords, region=region))
            return
        for child in node:
            walk(child, region)

    walk(root)
    return features


def counts(features: list[dict]) -> Counter:
    return Counter(feature["properties"]["kind"] for feature in features)


def feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}
