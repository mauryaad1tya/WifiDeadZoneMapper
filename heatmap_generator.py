from __future__ import annotations
from typing import List, Dict, Optional, Tuple
import folium
from folium.plugins import HeatMap
import numpy as np

from ai_model import predict_grid


def _scale_rssi(value: float, vmin: float = -95, vmax: float = -35) -> float:
    if value is None:
        return 0.0
    x = (value - vmin) / (vmax - vmin)
    return float(max(0.0, min(1.0, x)))


def build_heatmap_html(logs: List[Dict], model_path: str, grid_size: int = 32) -> str:
    preds, bounds = predict_grid(logs, model_path, grid_size=grid_size)
    # Fallback center if no data
    center = [20.0, 0.0]
    if bounds:
        lat_min, lon_min, lat_max, lon_max = bounds
        center = [(lat_min + lat_max) / 2.0, (lon_min + lon_max) / 2.0]

    m = folium.Map(location=center, zoom_start=14, tiles='cartodbdark_matter')

    # Observed
    obs = []
    for r in logs:
        try:
            lat = float(r.get('latitude'))
            lon = float(r.get('longitude'))
            rssi = float(r.get('rssi_dbm'))
        except Exception:
            continue
        if lat is None or lon is None or rssi is None:
            continue
        obs.append([lat, lon, _scale_rssi(rssi)])
    if obs:
        HeatMap(obs, name='Observed', min_opacity=0.3, radius=18, blur=25, gradient={0.0:'red',0.5:'yellow',1.0:'lime'}).add_to(m)

    # Predicted
    pred = []
    for p in preds:
        pred.append([p['latitude'], p['longitude'], _scale_rssi(p.get('rssi_pred'))])
    if pred:
        HeatMap(pred, name='Predicted', min_opacity=0.2, radius=16, blur=22, gradient={0.0:'red',0.5:'yellow',1.0:'lime'}, show=False).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m.get_root().render()
