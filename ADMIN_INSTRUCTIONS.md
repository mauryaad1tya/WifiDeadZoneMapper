# How to Scan All Wi-Fi Networks

## The Issue
Windows requires **Administrator privileges** to scan all available Wi-Fi networks using `netsh wlan show networks`.

## Solution: Run as Administrator

### Option 1: Using the Batch File (Easiest)
1. Right-click `run_as_admin.bat`
2. Select **"Run as administrator"**
3. Open http://127.0.0.1:5001
4. Click "🔄 Refresh Networks" to see all available networks

### Option 2: PowerShell/CMD
1. Right-click **PowerShell** or **Command Prompt**
2. Select **"Run as administrator"**
3. Navigate to project folder:
   ```
   cd "d:\All\Projects\WIFI\AI_WiFi_DeadZone_Mapper"
   ```
4. Run the app:
   ```
   python app.py
   ```
5. Open http://127.0.0.1:5001
6. Click "🔄 Refresh Networks"

### Option 3: VS Code Terminal
1. Open VS Code as Administrator:
   - Right-click VS Code icon → "Run as administrator"
2. Open terminal in VS Code
3. Run: `python app.py`
4. Open http://127.0.0.1:5001

## What You'll See

When running **without admin**:
- ⚠️ "Admin Required" message
- Can still use demo data and view heatmap

When running **with admin**:
- ✅ List of all nearby Wi-Fi networks
- 🟢 Green = Strong signal (-60 dBm or better)
- 🟡 Yellow = Medium signal (-75 to -60 dBm)
- 🔴 Red = Weak signal (below -75 dBm)

## Features Available
- **Scan Strongest Network**: Automatically picks the best signal
- **View all networks**: See SSID, RSSI (dBm), and signal percentage
- **Heatmap**: Train AI and visualize coverage
- **AI Report**: Get recommendations for improving coverage
