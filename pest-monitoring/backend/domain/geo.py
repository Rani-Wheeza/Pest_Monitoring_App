"""Map helpers (Task 8.3): bounding boxes, heat weights and GeoJSON output."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

HEAT_WEIGHTS = {"High": 3, "Medium": 2, "Low": 1}


@dataclass(frozen=True)
class BoundingBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def contains(self, lon: float, lat: float) -> bool:
        return self.min_lon <= lon <= self.max_lon and self.min_lat <= lat <= self.max_lat


def parse_bbox(text: str) -> BoundingBox:
    """Parse "minLon,minLat,maxLon,maxLat" as sent by Azure Maps."""
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox needs four numbers: minLon,minLat,maxLon,maxLat")
    min_lon, min_lat, max_lon, max_lat = (float(p) for p in parts)
    if not (-180 <= min_lon <= max_lon <= 180 and -90 <= min_lat <= max_lat <= 90):
        raise ValueError("bbox is outside the valid range or the wrong way round")
    return BoundingBox(min_lon, min_lat, max_lon, max_lat)


def heat_weight(priority: str | None) -> int:
    return HEAT_WEIGHTS.get(priority or "", 1)


def to_feature_collection(rows: Iterable[Mapping]) -> dict:
    """Build GeoJSON for the Azure Maps data source. Each row needs latitude/longitude."""
    features = []
    for row in rows:
        properties = {k: v for k, v in row.items() if k not in ("latitude", "longitude")}
        properties["heat_weight"] = heat_weight(row.get("priority"))
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(row["longitude"]), float(row["latitude"])]},
            "properties": properties,
        })
    return {"type": "FeatureCollection", "features": features}
