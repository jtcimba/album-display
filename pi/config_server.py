from flask import Flask, request, jsonify, render_template_string
import threading
import os

class ConfigServer:
    def __init__(self, config_callback):
        self.app = Flask(__name__)
        self.config_callback = config_callback
        self.server_thread = None
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string(self.get_html_template())
        
        @self.app.route('/config', methods=['POST'])
        def handle_config():
            try:
                data = request.json
                print(f"Received config: {data}")
                response = self.config_callback(data)
                return jsonify(response)
            except Exception as e:
                print(f"Config error: {e}")
                return jsonify({'success': False, 'errors': {'server': str(e)}}), 500
        
        @self.app.route('/status', methods=['GET'])
        def get_status():
            return jsonify({'ready': True, 'version': '1.0'})
    
    def get_html_template(self):
        """Return the configuration web page HTML"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Album Display Configuration</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
            padding: 40px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
            display: flex;
            align-items: center;
        }
        
        .section-icon {
            margin-right: 8px;
            font-size: 20px;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 15px;
            margin-bottom: 10px;
            transition: border-color 0.3s;
        }
        
        input[type="checkbox"] {
            width: 20px;
            height: 20px;
            margin-right: 10px;
            cursor: pointer;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-primary:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .status {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        
        .status.show {
            display: block;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .helper-text {
            font-size: 13px;
            color: #666;
            margin-top: 5px;
        }
        
        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
            margin-left: 8px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .info-box {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .test-mode-box {
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 8px;
            border: 1px solid #ffc107;
        }
        
        .test-mode-box label {
            display: flex;
            align-items: center;
            cursor: pointer;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Album Display</h1>
        <p class="subtitle">Configure your audio sources</p>
        
        <div class="info-box">
            💡 This configuration page is always available at <strong>http://10.0.0.195</strong>
        </div>
        
        <div id="status" class="status"></div>
        
        <!-- WiiM Section -->
        <div class="section">
            <h3>
                <span class="section-icon">📻</span>
                WiiM Device
            </h3>
            
            <input type="text" id="wiim" placeholder="WiiM IP Address (optional for testing)">
            <p class="helper-text">Find WiiM IP in the WiiM app settings → Device Info</p>
        </div>
        
        <!-- Test Mode Section -->
        <div class="test-mode-box">
            <label>
                <input type="checkbox" id="test-mode">
                <span><strong>Test Mode</strong> - Cycle through colored test images (for setup/testing)</span>
            </label>
        </div>
        
        <!-- Save Button -->
        <button class="btn-primary" id="saveBtn" onclick="saveConfig()">
            Save Configuration
        </button>
    </div>
    
    <script>
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.innerHTML = message;
            status.className = 'status ' + type + ' show';
        }
        
        function hideStatus() {
            document.getElementById('status').classList.remove('show');
        }
        
        async function saveConfig() {
            const wiim = document.getElementById('wiim').value.trim();
            const testMode = document.getElementById('test-mode').checked;
            
            
            // Build config object
            const config = {
                wiim_ip: wiim || null,
                test_mode: testMode
            };
            
            // Show loading state
            const btn = document.getElementById('saveBtn');
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = 'Saving<span class="loading"></span>';
            
            try {
                const response = await fetch('/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('✓ Configuration saved! Display will restart in 3 seconds...', 'success');
                    
                    // Disable form
                    document.querySelectorAll('input, button').forEach(el => el.disabled = true);
                    
                    // Show final message
                    setTimeout(() => {
                        showStatus('✓ Display restarting. Refresh this page in 10 seconds to reconfigure.', 'success');
                    }, 3000);
                } else {
                    let errorMsg = 'Configuration failed: ';
                    for (const [key, msg] of Object.entries(result.errors || {})) {
                        errorMsg += `${key}: ${msg}. `;
                    }
                    showStatus(errorMsg, 'error');
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                }
            } catch (err) {
                showStatus('Error: ' + err.message, 'error');
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
    </script>
</body>
</html>
        '''
    
    def start(self, host='0.0.0.0', port=80):
        """Start Flask server in background thread"""
        def run_server():
            self.app.run(host=host, port=port, debug=False, threaded=True)
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"✓ Config server started on http://{host}:{port}")
    
    def stop(self):
        """Stop the server (Flask doesn't support clean shutdown in thread)"""
        print("Config server will stop when process exits")
