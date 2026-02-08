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
    <title>Album Display Setup</title>
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
        
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 15px;
            margin-bottom: 10px;
            transition: border-color 0.3s;
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
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
            margin-bottom: 10px;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
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
        
        .connected-badge {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Album Display</h1>
        <p class="subtitle">Configure your album art display</p>
        
        <div id="status" class="status"></div>
        
        <!-- WiFi Section -->
        <div class="section">
            <h3>
                <span class="section-icon">📶</span>
                WiFi Network
            </h3>
            <input type="text" id="ssid" placeholder="Network Name (SSID)" required>
            <input type="password" id="password" placeholder="WiFi Password" required>
        </div>
        
        <!-- Audio Source Section -->
        <div class="section">
            <h3>
                <span class="section-icon">🎵</span>
                Audio Source
                <span id="audio-connected" class="connected-badge" style="display: none;">Connected</span>
            </h3>
            
            <button class="btn-secondary" onclick="connectSpotify()">
                Connect Spotify Account
            </button>
            
            <input type="text" id="wiim" placeholder="WiiM IP Address (optional)">
            <p class="helper-text">Find WiiM IP in the WiiM app settings. Leave blank if using Spotify only.</p>
        </div>
        
        <!-- Save Button -->
        <button class="btn-primary" id="saveBtn" onclick="saveConfig()">
            Save Configuration
        </button>
    </div>
    
    <script>
        let spotifyTokens = null;
        
        // Check for Spotify tokens in URL (after OAuth redirect)
        const params = new URLSearchParams(window.location.search);
        if (params.has('access_token')) {
            spotifyTokens = {
                access_token: params.get('access_token'),
                refresh_token: params.get('refresh_token'),
                expires_in: params.get('expires_in')
            };
            document.getElementById('audio-connected').style.display = 'inline-block';
            showStatus('Spotify account connected!', 'success');
            
            // Clean URL
            window.history.replaceState({}, document.title, '/');
        }
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type + ' show';
        }
        
        function hideStatus() {
            document.getElementById('status').classList.remove('show');
        }
        
        function connectSpotify() {
            showStatus('Redirecting to Spotify...', 'info');
            
            // TODO: Replace with your Spotify Client ID
            const clientId = 'YOUR_SPOTIFY_CLIENT_ID';
            const redirectUri = window.location.origin + '/spotify-callback';
            const scopes = 'user-read-currently-playing user-read-playback-state';
            
            const authUrl = 'https://accounts.spotify.com/authorize?' +
                'client_id=' + encodeURIComponent(clientId) +
                '&response_type=code' +
                '&redirect_uri=' + encodeURIComponent(redirectUri) +
                '&scope=' + encodeURIComponent(scopes);
            
            window.location.href = authUrl;
        }
        
        async function saveConfig() {
            const ssid = document.getElementById('ssid').value.trim();
            const password = document.getElementById('password').value;
            const wiim = document.getElementById('wiim').value.trim();
            
            // Validation
            if (!ssid) {
                showStatus('Please enter WiFi network name', 'error');
                return;
            }
            
            if (!password) {
                showStatus('Please enter WiFi password', 'error');
                return;
            }
            
            if (!spotifyTokens && !wiim) {
                showStatus('Please connect Spotify or enter WiiM IP address', 'error');
                return;
            }
            
            // Build config object
            const config = {
                wifi_ssid: ssid,
                wifi_password: password,
                wiim_ip: wiim || null
            };
            
            // Add Spotify tokens if available
            if (spotifyTokens) {
                config.spotify_access_token = spotifyTokens.access_token;
                config.spotify_refresh_token = spotifyTokens.refresh_token;
                config.spotify_token_expiry = Date.now() + (spotifyTokens.expires_in * 1000);
            }
            
            // Show loading state
            const btn = document.getElementById('saveBtn');
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = 'Configuring<span class="loading"></span>';
            
            try {
                const response = await fetch('/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('✓ Configuration saved! Device is connecting to your WiFi...', 'success');
                    
                    // Disable form
                    document.querySelectorAll('input, button').forEach(el => el.disabled = true);
                    
                    // Show final message
                    setTimeout(() => {
                        showStatus('✓ Setup complete! Your album display is now running. You can close this page.', 'success');
                    }, 3000);
                } else {
                    let errorMsg = 'Configuration failed:\n';
                    for (const [key, msg] of Object.entries(result.errors || {})) {
                        errorMsg += `${key}: ${msg}\n`;
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
        
        // Enable save button when form is filled
        function checkForm() {
            const ssid = document.getElementById('ssid').value;
            const password = document.getElementById('password').value;
            const hasAudio = spotifyTokens || document.getElementById('wiim').value;
            
            document.getElementById('saveBtn').disabled = !(ssid && password && hasAudio);
        }
        
        document.getElementById('ssid').addEventListener('input', checkForm);
        document.getElementById('password').addEventListener('input', checkForm);
        document.getElementById('wiim').addEventListener('input', checkForm);
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