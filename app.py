from __future__ import annotations
import os
import csv
from datetime import datetime
from typing import List, Dict, Optional

from flask import Flask, render_template, request, jsonify

from ai_model import ensure_model, train_model, predict_grid, generate_ai_report
from heatmap_generator import build_heatmap_html
from data_collector import scan_once, _scan_windows_all

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_ROOT, 'data')
MODELS_DIR = os.path.join(APP_ROOT, 'models')
LOG_PATH = os.path.join(DATA_DIR, 'wifi_logs.csv')
MODEL_PATH = os.path.join(MODELS_DIR, 'wifi_predictor.pkl')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

app = Flask(
    __name__,
    template_folder=os.path.join(APP_ROOT, 'templates'),
    static_folder=os.path.join(APP_ROOT, 'static'),
)

CSV_FIELDS = ['timestamp', 'ssid', 'rssi_dbm', 'latitude', 'longitude']


def _read_logs() -> List[Dict]:
    rows: List[Dict] = []
    if not os.path.exists(LOG_PATH):
        return rows
    with open(LOG_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def _append_log(row: Dict) -> None:
    new_file = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


@app.route('/')
def index():
    logs = _read_logs()
    avg = None
    cur = None
    if logs:
        try:
            vals = [float(r['rssi_dbm']) for r in logs if r.get('rssi_dbm') is not None and r['rssi_dbm'] != '']
            if vals:
                avg = round(sum(vals) / len(vals), 1)
                cur = vals[-1]
        except Exception:
            pass
    stats = {
        'count': len(logs),
        'avg_rssi': avg,
        'last_update': logs[-1]['timestamp'] if logs else None,
        'current_signal': cur,
    }
    return render_template('index.html', stats=stats)


@app.route('/heatmap')
def heatmap_page():
    logs = _read_logs()
    html = build_heatmap_html(logs, MODEL_PATH)
    return render_template('heatmap.html', map_html=html)


@app.route('/ai-report')
def ai_report_page():
    logs = _read_logs()
    report = generate_ai_report(logs, MODEL_PATH)
    return render_template('ai_report.html', report_text=report)


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/api/scan', methods=['POST'])
def api_scan():
    data = request.get_json(silent=True) or {}
    lat = data.get('lat')
    lon = data.get('lon')
    reading = scan_once(lat=lat, lon=lon)
    if not reading:
        return jsonify({'ok': False, 'error': 'scan_failed'}), 500
    row = {
        'timestamp': datetime.utcnow().isoformat(),
        'ssid': reading.get('ssid') or '',
        'rssi_dbm': reading.get('rssi_dbm'),
        'latitude': reading.get('latitude'),
        'longitude': reading.get('longitude'),
    }
    _append_log(row)
    return jsonify({'ok': True, 'inserted': 1, 'row': row})


@app.route('/api/train', methods=['POST'])
def api_train():
    data = request.get_json(silent=True) or {}
    model_type = (data.get('model_type') or 'rf').lower()  # 'rf' or 'mlp'
    logs = _read_logs()
    ok, info = train_model(logs, MODEL_PATH, model_type=model_type)
    return jsonify({'ok': ok, 'info': info})


@app.route('/api/predict', methods=['GET'])
def api_predict():
    logs = _read_logs()
    preds, bounds = predict_grid(logs, MODEL_PATH, grid_size=int(request.args.get('grid', 32)))
    # Count predicted weak zones
    weak_thr = float(request.args.get('weak', -80))
    weak_count = int(sum(1 for p in preds if p.get('rssi_pred', -999) < weak_thr))
    return jsonify({'preds': preds, 'bounds': bounds, 'weak_count': weak_count})


@app.route('/api/stats', methods=['GET'])
def api_stats():
    logs = _read_logs()
    avg = None
    cur = None
    if logs:
        try:
            vals = [float(r['rssi_dbm']) for r in logs if r.get('rssi_dbm') not in (None, '')]
            if vals:
                avg = round(sum(vals) / len(vals), 1)
                cur = vals[-1]
        except Exception:
            pass
    return jsonify({'count': len(logs), 'avg_rssi': avg, 'current_signal': cur, 'last_update': logs[-1]['timestamp'] if logs else None})


@app.route('/api/networks', methods=['GET'])
def api_networks():
    """Get all available Wi-Fi networks"""
    import sys
    if sys.platform.startswith("win"):
        networks = _scan_windows_all()
        if len(networks) == 0:
            return jsonify({
                'networks': [], 
                'count': 0, 
                'error': 'admin_required',
                'message': 'Run PowerShell/CMD as Administrator to scan all networks'
            })
        return jsonify({'networks': networks, 'count': len(networks)})
    return jsonify({'networks': [], 'count': 0, 'error': 'Only Windows supported for now'})


if __name__ == '__main__':
    # Prefer waitress in production-like mode
    try:
        from waitress import serve
        serve(app, host='0.0.0.0', port=int(os.getenv('PORT', 5001)))
    except Exception:
        app.run(debug=True, host='0.0.0.0', port=5001)
