(function(){
  const $ = (sel)=>document.querySelector(sel);
  const btn = $('#btnScan');
  const btnRefresh = $('#btnRefreshNetworks');
  const networksList = $('#networksList');
  const statusBox = $('#scanStatus');
  const lat = $('#lat');
  const lon = $('#lon');

  function showStatus(msg, cls='info'){
    statusBox.className = `alert alert-${cls}`;
    statusBox.textContent = msg;
    statusBox.classList.remove('d-none');
  }
  function hideStatus(){ statusBox.classList.add('d-none'); }

  async function refreshNetworks(){
    try{
      btnRefresh.disabled = true;
      networksList.innerHTML = '<span class="text-muted">Loading...</span>';
      const res = await fetch('/api/networks');
      const j = await res.json();
      if(j.error === 'admin_required'){
        networksList.innerHTML = `<div class="text-warning"><strong>⚠️ Admin Required</strong><br>${j.message}<br><small>Right-click PowerShell/CMD → "Run as Administrator" then restart: python app.py</small></div>`;
        return;
      }
      if(j.count === 0){
        networksList.innerHTML = '<span class="text-warning">No networks found. Ensure Wi-Fi is enabled.</span>';
        return;
      }
      let html = `<div class="text-success mb-1">✅ Found ${j.count} networks:</div>`;
      j.networks.forEach(n=>{
        const strength = n.rssi_dbm > -60 ? '🟢' : n.rssi_dbm > -75 ? '🟡' : '🔴';
        html += `<div class="small">${strength} <strong>${n.ssid}</strong> ${n.rssi_dbm} dBm (${n.signal_pct}%)</div>`;
      });
      networksList.innerHTML = html;
    }catch(e){
      networksList.innerHTML = '<span class="text-danger">Failed to fetch networks</span>';
    }finally{
      btnRefresh.disabled = false;
    }
  }

  btnRefresh?.addEventListener('click', refreshNetworks);

  btn?.addEventListener('click', async ()=>{
    try{
      btn.disabled = true;
      showStatus('Scanning...');
      const payload = {
        lat: lat.value ? parseFloat(lat.value) : null,
        lon: lon.value ? parseFloat(lon.value) : null,
      };
      const res = await fetch('/api/scan', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const j = await res.json();
      if (!j.ok){ throw new Error(j.error || 'Scan failed'); }
      showStatus('Scan complete. Inserted 1 reading.', 'success');
      setTimeout(()=> hideStatus(), 2000);
    }catch(e){
      showStatus('Scan failed. Ensure Wi‑Fi command is available.', 'danger');
    }finally{
      btn.disabled = false;
    }
  });
})();
