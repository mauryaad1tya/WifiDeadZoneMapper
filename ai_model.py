from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import os
import pickle
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor


def _extract_xy(logs: List[Dict]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[Tuple[float, float, float, float]]]:
    if not logs:
        return None, None, None
    X_list = []
    y_list = []
    lats = []
    lons = []
    for r in logs:
        try:
            lat = float(r.get('latitude')) if r.get('latitude') not in (None, '') else None
            lon = float(r.get('longitude')) if r.get('longitude') not in (None, '') else None
            rssi = float(r.get('rssi_dbm')) if r.get('rssi_dbm') not in (None, '') else None
        except Exception:
            lat = lon = rssi = None
        if lat is None or lon is None or rssi is None:
            continue
        X_list.append([lat, lon])
        y_list.append(rssi)
        lats.append(lat)
        lons.append(lon)
    if not X_list:
        return None, None, None
    bounds = (min(lats), min(lons), max(lats), max(lons))
    return np.array(X_list, dtype=float), np.array(y_list, dtype=float), bounds


def train_model(logs: List[Dict], model_path: str, model_type: str = 'rf') -> Tuple[bool, str]:
    X, y, _ = _extract_xy(logs)
    if X is None or len(X) < 10:
        return False, 'insufficient_data'
    if model_type == 'mlp':
        model = MLPRegressor(hidden_layer_sizes=(64, 32), activation='relu', max_iter=500, random_state=42)
    else:
        model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(X, y)
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump({'type': model_type, 'model': model}, f)
    return True, 'trained'


def ensure_model(logs: List[Dict], model_path: str, model_type: str = 'rf') -> bool:
    if os.path.exists(model_path):
        return True
    ok, _ = train_model(logs, model_path, model_type)
    return ok


def _load_model(model_path: str):
    if not os.path.exists(model_path):
        return None
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def predict_grid(logs: List[Dict], model_path: str, grid_size: int = 32) -> Tuple[List[Dict], Optional[Tuple[float, float, float, float]]]:
    X, y, bounds = _extract_xy(logs)
    if X is None or bounds is None:
        return [], None
    mdl = _load_model(model_path)
    if mdl is None:
        ok = ensure_model(logs, model_path)
        if not ok:
            return [], bounds
        mdl = _load_model(model_path)
    model = mdl['model']
    lat_min, lon_min, lat_max, lon_max = bounds
    lat_lin = np.linspace(lat_min, lat_max, grid_size)
    lon_lin = np.linspace(lon_min, lon_max, grid_size)
    glat, glon = np.meshgrid(lat_lin, lon_lin)
    grid_pts = np.column_stack([glat.ravel(), glon.ravel()])
    preds = model.predict(grid_pts)
    out = [
        {'latitude': float(lat), 'longitude': float(lon), 'rssi_pred': float(val)}
        for (lat, lon), val in zip(grid_pts, preds)
    ]
    return out, bounds


def generate_ai_report(logs: List[Dict], model_path: str) -> str:
    # Simple rules-based summary; if model and predictions available, include weak hotspots
    preds, bounds = predict_grid(logs, model_path, grid_size=32)
    total = len(logs)
    ssids = sorted(set([r.get('ssid') or '' for r in logs]))
    rssi_vals = [float(r['rssi_dbm']) for r in logs if r.get('rssi_dbm') not in (None, '')]
    avg = sum(rssi_vals) / len(rssi_vals) if rssi_vals else None

    lines = []
    lines.append('AI Wi‑Fi Insights Report')
    lines.append('=========================')
    lines.append('')
    lines.append(f'Total readings: {total}')
    lines.append(f'Unique SSIDs: {len(ssids)}')
    if avg is not None:
        lines.append(f'Average RSSI: {avg:.1f} dBm')
    lines.append('')

    if preds:
        weak_thr = -80.0
        weak_spots = sorted([p for p in preds if p['rssi_pred'] < weak_thr], key=lambda x: x['rssi_pred'])[:5]
        if weak_spots:
            lines.append('Predicted dead zones (weak signal):')
            for p in weak_spots:
                lines.append(f" - ({p['latitude']:.5f}, {p['longitude']:.5f}) around {p['rssi_pred']:.1f} dBm")
        else:
            lines.append('No strong dead zones predicted. Coverage appears acceptable.')
    else:
        lines.append('Insufficient data for predictions. Collect more points and retrain the model.')
    lines.append('')

    lines.append('Recommendations:')
    lines.append('- Add or reposition access points near predicted weak areas.')
    lines.append('- Reduce obstructions (walls, metal) along client-to-AP paths.')
    lines.append('- Prefer 2.4 GHz for range, 5 GHz for speed as needed.')
    return '\n'.join(lines)
