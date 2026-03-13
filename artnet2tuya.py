import time
import json
import threading
import os
import colorsys
from datetime import datetime
from flask import Flask, render_template_string, request, redirect
from stupidArtnet import StupidArtnetServer
import tinytuya

app = Flask(__name__)
CONFIG_FILE = 'config.json'

def rgb_to_tuya_hsv(r, g, b, brightness_dmx):
    """converts RGB + DMX-Dimmer into the Tuya HSV Hex-Format."""
    h, s, _ = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    v_scaled = int((brightness_dmx / 255) * 1000)
    v_scaled = max(10, min(1000, v_scaled)) 
    return f"{int(h*360):04x}{int(s*1000):04x}{v_scaled:04x}"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"universe": 0, "devices": []}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

# Global variables
bridge_config = load_config()
active_devices = {}  
running = True

def update_bridge_devices():
    """Maintains persistent TCP connections to the bulbs for low latency."""
    global active_devices
    conf = load_config()
    new_devices = {}
    for dev in conf['devices']:
        if dev.get('enabled') and dev.get('key') and dev.get('key') != "REQUIRED":
            try:
                if dev['id'] in active_devices:
                    active_devices[dev['id']]['start_ch'] = dev['start_ch']
                    active_devices[dev['id']]['is_rgb'] = dev['is_rgb']
                    new_devices[dev['id']] = active_devices[dev['id']]
                else:
                    d = tinytuya.BulbDevice(dev['id'], dev['ip'], dev['key'])
                    d.set_version(float(dev.get('version', 3.3)))
                    d.set_socketRetryLimit(5)
                    d.status() 
                    new_devices[dev['id']] = {
                        'obj': d,
                        'last_data': [0]*6,
                        'start_ch': dev['start_ch'],
                        'is_rgb': dev['is_rgb']
                    }
                    print(f"✅ Persistent connection established: {dev['name']}")
            except Exception as e:
                print(f"❌ Connection failed for {dev.get('name')}: {e}")
    active_devices = new_devices

# ARTNET LISTENER THREAD
def artnet_worker():
    global bridge_config
    server = StupidArtnetServer()
    
    universe_val = bridge_config.get('universe', 0)
    server.register_listener(universe_val)
    print(f"🚀 ArtNet Listener active on Universe {universe_val}")
    
    while running:
        dmx_data = server.get_buffer(bridge_config.get('universe', 0))
        
        if dmx_data:
            for dev_id, light in active_devices.items():
                idx = light['start_ch'] - 1
                ch = dmx_data[idx : idx + 6]
                
                if len(ch) < 6 or list(ch) == light['last_data']:
                    continue
                
                light['last_data'] = list(ch)
                
                pwr = ch[0] > 127
                bri_raw = ch[1] 
                tmp_raw = ch[2]
                r, g, b = ch[3], ch[4], ch[5]
                
                payload = {'20': pwr}
                
                if pwr:
                    if light['is_rgb'] and (r > 5 or g > 5 or b > 5):
                        hsv_hex = rgb_to_tuya_hsv(r, g, b, bri_raw)
                        payload.update({
                            '21': 'colour',
                            '24': hsv_hex
                        })
                    else:
                        bri_t = max(10, int((bri_raw / 255) * 1000))
                        tmp_t = max(1, int((tmp_raw / 255) * 1000))
                        payload.update({
                            '21': 'white', 
                            '22': bri_t, 
                            '23': tmp_t
                        })

                try:
                    light['obj'].set_multiple_values(payload, nowait=True)
                except:
                    pass
        
        time.sleep(0.01)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ArtNet2Tuya SmartBridge</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
    <style> 
        .ch-head { background: #e9ecef; font-weight: bold; } 
        .font-monospace { font-family: monospace; }
        .row-disabled { opacity: 0.5; background-color: #f8f9fa; }
        .drag-handle { cursor: grab; color: #ccc; font-size: 1.2rem; user-select: none; }
        .drag-handle:active { cursor: grabbing; }
        .sortable-ghost { background-color: #e2e6ea; opacity: 0.8; }
    </style>
</head>
<body class="bg-light">
    <div class="container mt-4">
        <div class="card shadow-sm mb-4">
            <div class="card-body d-flex justify-content-between align-items-center">
                <h1 class="h3 mb-0">ArtNet2Tuya SmartBridge</h1>
                <form action="/save_universe" method="POST" class="d-flex align-items-center">
                    <label class="me-2">Universe:</label>
                    <input type="number" name="universe" value="{{ config.universe }}" class="form-control me-2" style="width: 80px;">
                    <button type="submit" class="btn btn-dark">Update</button>
                </form>
            </div>
        </div>

        <div class="card shadow-sm mb-4">
            <div class="card-header bg-primary text-white">Device Configuration</div>
            <div class="card-body">
                <form action="/save_devices" method="POST" id="deviceForm">
                <table class="table align-middle">
                    <thead>
                        <tr>
                            <th>Order</th>
                            <th>Use</th>
                            <th>Name / Product</th>
                            <th>IP Address</th>
                            <th>Local Key</th>
                            <th>Ver</th>
                            <th>RGB?</th>
                            <th>Start CH</th>
                            <th>X</th>
                        </tr>
                    </thead>
                    <tbody id="deviceTableBody">
                        {% for dev in config.devices %}
                        <tr class="device-row {{ '' if dev.enabled else 'row-disabled' }}">
                            <td class="drag-handle text-center">☰</td>
                            <td>
                                <input type="checkbox" class="use-check" name="enabled_{{ loop.index0 }}" {{ 'checked' if dev.enabled }}>
                            </td>
                            <td>
                                <strong class="dev-name">{{ dev.name }}</strong><br>
                                <small class="text-muted">{{ dev.product }}</small>
                                <input type="hidden" name="id_{{ loop.index0 }}" value="{{ dev.id }}">
                                <input type="hidden" name="name_{{ loop.index0 }}" value="{{ dev.name }}">
                                <input type="hidden" name="product_{{ loop.index0 }}" value="{{ dev.product }}">
                                <input type="hidden" name="ip_{{ loop.index0 }}" value="{{ dev.ip }}">
                            </td>
                            <td><code class="small">{{ dev.ip }}</code></td>
                            <td><input type="text" name="key_{{ loop.index0 }}" value="{{ dev.key }}" class="form-control form-control-sm font-monospace" style="font-size: 0.75rem;"></td>
                            <td><input type="number" step="0.1" name="version_{{ loop.index0 }}" value="{{ dev.version }}" class="form-control form-control-sm" style="width:55px;"></td>
                            <td><input type="checkbox" class="rgb-check" name="is_rgb_{{ loop.index0 }}" {{ 'checked' if dev.is_rgb }}></td>
                            <td>
                                <input type="number" name="start_ch_{{ loop.index0 }}" value="{{ dev.start_ch }}" class="form-control form-control-sm start-ch-input" style="width:70px;" readonly>
                            </td>
                            <td><a href="/delete/{{ loop.index0 }}" class="btn btn-outline-danger btn-sm">×</a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                <div class="d-flex justify-content-between mt-3">
                    <button type="submit" class="btn btn-success px-4">Save & Apply Changes</button>
                    <div>
                        <a href="/scan" class="btn btn-outline-primary me-2">Scan Network</a>
                    </div>
                </div>
                </form>
                <hr>
                <form action="/upload_json" method="POST" enctype="multipart/form-data" class="row g-3">
                    <div class="col-auto">
                        <label class="col-form-label">Update devices.json:</label>
                    </div>
                    <div class="col-auto">
                        <input type="file" name="file" class="form-control form-control-sm" accept=".json">
                    </div>
                    <div class="col-auto">
                        <button type="submit" class="btn btn-sm btn-secondary">Upload & Backup</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="card shadow-sm mb-5">
            <div class="card-header bg-secondary text-white">xLights / QLC+ Patching Guide (Universe {{ config.universe }})</div>
            <div class="card-body p-0">
                <table class="table table-sm mb-0">
                    <thead class="table-light">
                        <tr><th>Channel</th><th>Function</th><th>DMX Range</th></tr>
                    </thead>
                    <tbody id="guideBody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const tableBody = document.getElementById('deviceTableBody');
        const guideBody = document.getElementById('guideBody');

        function updateUI() {
            let currentCh = 1;
            const rows = document.querySelectorAll('.device-row');
            guideBody.innerHTML = '';

            rows.forEach((row) => {
                const checkbox = row.querySelector('.use-check');
                const channelInput = row.querySelector('.start-ch-input');
                const name = row.querySelector('.dev-name').innerText;
                const isRGB = row.querySelector('.rgb-check').checked;
                
                if (checkbox.checked) {
                    channelInput.value = currentCh;
                    row.classList.remove('row-disabled');

                    guideBody.innerHTML += `
                        <tr class="ch-head"><td colspan="3">${name} (Starts @ Ch ${currentCh})</td></tr>
                        <tr><td>${currentCh}</td><td>Power</td><td>0-127 Off, 128-255 On</td></tr>
                        <tr><td>${currentCh + 1}</td><td>Dimmer</td><td>0-255</td></tr>
                        <tr><td>${currentCh + 2}</td><td>White Temp</td><td>Warm-Cold</td></tr>
                        <tr><td>${currentCh + 3}</td><td>Red</td><td>${isRGB ? '0-255' : 'N/A'}</td></tr>
                        <tr><td>${currentCh + 4}</td><td>Green</td><td>${isRGB ? '0-255' : 'N/A'}</td></tr>
                        <tr><td>${currentCh + 5}</td><td>Blue</td><td>${isRGB ? '0-255' : 'N/A'}</td></tr>
                    `;
                    currentCh += 6;
                } else {
                    channelInput.value = 0;
                    row.classList.add('row-disabled');
                }
            });
        }

        new Sortable(tableBody, {
            animation: 150,
            handle: '.drag-handle',
            ghostClass: 'sortable-ghost',
            onEnd: updateUI 
        });

        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('use-check') || e.target.classList.contains('rgb-check')) {
                updateUI();
            }
        });

        window.onload = updateUI;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, config=load_config())

@app.route('/save_universe', methods=['POST'])
def save_universe():
    global bridge_config
    conf = load_config()
    conf['universe'] = int(request.form['universe'])
    save_config(conf)
    bridge_config = conf
    return redirect('/')

@app.route('/save_devices', methods=['POST'])
def save_devices():
    new_device_list = []
    keys = [k for k in request.form.keys() if k.startswith('id_')]
    indices = [k.split('_')[1] for k in keys]

    current_ch = 1
    for i in indices:
        enabled = f'enabled_{i}' in request.form
        start_ch = 0
        if enabled:
            start_ch = current_ch
            current_ch += 6
            
        dev = {
            "id": request.form.get(f'id_{i}'),
            "name": request.form.get(f'name_{i}'),
            "product": request.form.get(f'product_{i}'),
            "ip": request.form.get(f'ip_{i}'),
            "key": request.form.get(f'key_{i}'),
            "version": float(request.form.get(f'version_{i}', 3.3)),
            "is_rgb": f'is_rgb_{i}' in request.form,
            "enabled": enabled,
            "start_ch": start_ch
        }
        new_device_list.append(dev)

    conf = load_config()
    conf['devices'] = new_device_list
    save_config(conf)
    update_bridge_devices()
    return redirect('/')

@app.route('/delete/<int:index>')
def delete(index):
    conf = load_config()
    if 0 <= index < len(conf['devices']):
        conf.get('devices').pop(index)
        save_config(conf)
        update_bridge_devices()
    return redirect('/')

@app.route('/scan')
def scan():
    print("🔍 Scanning local network and matching with devices.json...")
    tuya_db = []
    if os.path.exists('devices.json'):
        try:
            with open('devices.json', 'r') as f:
                data = json.load(f)
                tuya_db = data.get('devices', data) if isinstance(data, dict) else data
        except Exception as e:
            print(f"Error reading devices.json: {e}")

    try:
        online_data = tinytuya.deviceScan(duration=5)
    except:
        online_data = tinytuya.deviceScan()
        
    conf = load_config()
    existing_ids = [d['id'] for d in conf['devices']]
    
    for dev_id, net_info in online_data.items():
        real_id = net_info.get('gwId', net_info.get('id', dev_id))
        if real_id not in existing_ids:
            match = next((d for d in tuya_db if d['id'] == real_id), None)
            if match:
                new_dev = {
                    "name": match.get('name', 'Unknown'),
                    "product": match.get('product_name', 'Generic Bulb'),
                    "id": real_id,
                    "ip": net_info.get('ip', match.get('ip', '0.0.0.0')),
                    "key": match.get('key', ''),
                    "version": match.get('ver', net_info.get('ver', 3.3)),
                    "is_rgb": True,
                    "enabled": False,
                    "start_ch": (len(conf['devices']) * 6) + 1
                }
                conf['devices'].append(new_dev)
                print(f"✅ Found and Matched: {new_dev['name']}")
            
    save_config(conf)
    return redirect('/')

@app.route('/upload_json', methods=['POST'])
def upload_json():
    if 'file' not in request.files:
        return redirect('/')
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.json'):
        return redirect('/')
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(base_dir, 'devices.json')
    config_path = os.path.join(base_dir, CONFIG_FILE)
    

    if os.path.exists(save_path):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.rename(save_path, os.path.join(base_dir, f"devices_backup_{ts}.json"))
    file.save(save_path)
    

    if os.path.exists(config_path):
        try:
            os.remove(config_path)
            print("🗑️ Existing config.json deleted to ensure clean scan with new data.")
        except Exception as e:
            print(f"Error deleting config: {e}")

    print(f"📁 devices.json updated. Redirecting to home for a fresh scan.")
    return redirect('/')

if __name__ == '__main__':
    update_bridge_devices()
    threading.Thread(target=artnet_worker, daemon=True).start()
    print("🌍 Web Interface running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)