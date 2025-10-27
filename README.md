# AI Wi‑Fi Dead Zone Mapper

A full‑stack Flask app that scans Wi‑Fi RSSI, logs with location, trains AI (RandomForest/MLP) to predict dead zones, and renders an interactive heatmap. Dark glassmorphism hacker UI with neon accents.

## Features
- **Data collection**: Windows (`netsh wlan show interfaces`) or macOS (`airport -I`)
- **Storage**: CSV at `data/wifi_logs.csv`
- **ML**: RandomForest (default) or MLP; model saved at `models/wifi_predictor.pkl`
- **Visualization**: Folium heatmap for observed + predicted
- **Dashboard**: Live scan, heatmap, AI insights, About

## Quickstart
```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5001

**⚠️ To scan ALL Wi-Fi networks:** Run as Administrator  
- Right-click `run_as_admin.bat` → "Run as administrator"  
- OR: Right-click PowerShell → "Run as administrator" → `python app.py`  
- See `ADMIN_INSTRUCTIONS.md` for details

## Usage
- Home: click **Start Scan** (optionally set lat/lon)
- Heatmap: click **Train AI** (RandomForest) then explore layers
- AI Insights: view a human‑readable summary of weak areas

## Tech Stack
- Flask, scikit‑learn, numpy, pandas, folium
- HTML/CSS/JS (glassmorphism theme)

## Files
- `app.py`: Flask routes and API
- `data_collector.py`: OS scanning and geo fallback
- `ai_model.py`: train, predict, report
- `heatmap_generator.py`: Folium map build
- `templates/`: `index.html`, `heatmap.html`, `ai_report.html`, `about.html`
- `static/css/style.css`, `static/js/script.js`
- `models/wifi_predictor.pkl` (created after training)
- `data/wifi_logs.csv` (appends as you scan)
