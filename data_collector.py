from __future__ import annotations
import subprocess
import sys
import re
from shutil import which
from typing import Optional, Dict
import requests


def _ip_geolocation() -> Optional[tuple[float, float]]:
    try:
        r = requests.get("http://ip-api.com/json/", timeout=5)
        if r.status_code == 200:
            j = r.json()
            lat = j.get("lat")
            lon = j.get("lon")
            if lat is not None and lon is not None:
                return float(lat), float(lon)
    except Exception:
        return None
    return None


def _scan_windows_all() -> list[Dict]:
    """Scan ALL available Wi-Fi networks on Windows"""
    if not which("netsh"):
        return []
    try:
        proc = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
    except Exception:
        return []
    
    out = proc.stdout
    
    # Check for permission errors
    if "requires elevation" in out.lower() or "location permission" in out.lower():
        return []
    
    networks = []
    current_ssid = None
    current_bssid = None
    
    for line in out.splitlines():
        line = line.strip()
        
        # Match SSID line (starts new network)
        ssid_match = re.match(r"^SSID\s+\d+\s*:\s*(.*)$", line, re.IGNORECASE)
        if ssid_match:
            current_ssid = ssid_match.group(1).strip()
            current_bssid = None
            continue
        
        # Match BSSID (MAC address)
        bssid_match = re.match(r"^BSSID\s+\d+\s*:\s*([0-9a-fA-F:]{17})$", line, re.IGNORECASE)
        if bssid_match:
            current_bssid = bssid_match.group(1)
            continue
        
        # Match Signal percentage
        signal_match = re.match(r"^Signal\s*:\s*(\d+)%$", line, re.IGNORECASE)
        if signal_match and current_ssid:
            signal_pct = int(signal_match.group(1))
            rssi_dbm = (signal_pct / 2.0) - 100.0
            networks.append({
                "ssid": current_ssid if current_ssid else "Hidden",
                "bssid": current_bssid,
                "rssi_dbm": float(rssi_dbm),
                "signal_pct": signal_pct
            })
    
    return networks


def _scan_windows() -> Optional[Dict]:
    """Get the strongest network from all available"""
    networks = _scan_windows_all()
    if not networks:
        return None
    # Return the strongest signal
    strongest = max(networks, key=lambda n: n.get('rssi_dbm', -999))
    return strongest


def _scan_macos() -> Optional[Dict]:
    airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    if not which(airport):
        return None
    try:
        proc = subprocess.run([airport, "-I"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    except Exception:
        return None
    out = proc.stdout
    ssid = None
    rssi = None
    for line in out.splitlines():
        line = line.strip()
        m1 = re.match(r"^SSID:\s*(.*)$", line)
        if m1:
            ssid = m1.group(1).strip()
        m2 = re.match(r"^agrCtlRSSI:\s*(-?\d+)$", line)
        if m2:
            try:
                rssi = float(m2.group(1))
            except Exception:
                rssi = None
    if rssi is None:
        return None
    return {"ssid": ssid, "rssi_dbm": rssi}


def scan_once(lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[Dict]:
    reading = None
    # Termux on Android: use termux-wifi-connectioninfo for current network RSSI
    if which("termux-wifi-connectioninfo"):
        try:
            proc = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
            import json
            j = json.loads(proc.stdout or '{}')
            ssid = j.get('ssid')
            rssi = j.get('rssi')  # negative dBm
            if rssi is not None:
                reading = {"ssid": ssid, "rssi_dbm": float(rssi)}
        except Exception:
            reading = None
    if sys.platform.startswith("win"):
        reading = _scan_windows()
    elif sys.platform == "darwin":
        reading = _scan_macos()
    else:
        # Optional: try Termux or Linux commands here (not required by prompt)
        reading = reading
    if reading is None:
        return None
    if lat is None or lon is None:
        loc = _ip_geolocation()
        if loc:
            lat, lon = loc
    reading.update({
        "latitude": float(lat) if lat is not None else None,
        "longitude": float(lon) if lon is not None else None,
    })
    return reading
