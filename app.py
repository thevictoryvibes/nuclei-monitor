from flask import Flask, request, jsonify
import subprocess
import json
import os
import tempfile
from datetime import datetime

app = Flask(__name__)

def run_nuclei_scan(url, templates):
    """Run Nuclei scanner on a single URL"""
    try:
        # Create temporary file for results
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        # Build nuclei command
        cmd = [
            'nuclei',
            '-u', url,
            '-t', templates,
            '-json',
            '-o', tmp_path,
            '-silent',
            '-timeout', '10',
            '-retries', '1'
        ]
        
        print(f"Running scan on: {url}")
        
        # Run nuclei
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Read results
        results = []
        if os.path.exists(tmp_path):
            with open(tmp_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except:
                            pass
            os.unlink(tmp_path)
        
        return {
            'success': True,
            'url': url,
            'vulnerabilities': results,
            'count': len(results),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'url': url,
            'error': 'Scan timeout',
            'vulnerabilities': [],
            'count': 0
        }
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'error': str(e),
            'vulnerabilities': [],
            'count': 0
        }

@app.route('/')
def home():
    """API Documentation"""
    docs = {
        'name': 'Nuclei Scanner API',
        'version': '1.0.0',
        'status': 'operational',
        'endpoints': {
            'GET /': 'API Documentation',
            'GET /health': 'Health Check',
            'POST /scan': 'Run Vulnerability Scan'
        },
        'usage': {
            'method': 'POST',
            'url': '/scan',
            'body': {
                'url': 'https://example.com',
                'templates': 'takeovers/'
            }
        }
    }
    return jsonify(docs)

@app.route('/health')
def health():
    """Health check endpoint"""
    nuclei_installed = os.path.exists('/usr/local/bin/nuclei')
    
    return jsonify({
        'status': 'healthy',
        'service': 'nuclei-scanner',
        'timestamp': datetime.utcnow().isoformat(),
        'nuclei_installed': nuclei_installed
    })

@app.route('/scan', methods=['POST'])
def scan():
    """
    Scan endpoint
    Expected JSON body:
    {
        "url": "https://example.com",
        "templates": "takeovers/" (optional, default: takeovers/)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing required parameter: url'
            }), 400
        
        url = data['url']
        templates = data.get('templates', 'takeovers/')
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            return jsonify({
                'error': 'Invalid URL format. Must start with http:// or https://'
            }), 400
        
        # Run scan
        result = run_nuclei_scan(url, templates)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Scan failed: {str(e)}',
            'success': False
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting Nuclei Scanner API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
