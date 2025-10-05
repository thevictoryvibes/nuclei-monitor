from flask import Flask, request, jsonify
import subprocess
import json
import os
import tempfile
from datetime import datetime

app = Flask(__name__)

def run_nuclei_scan(url, templates):
    try:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
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
        
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
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
    docs = {
        'name': 'Nuclei Scanner API',
        'version': '1.0.0',
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
        },
        'status': 'operational'
    }
    return jsonify(docs)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'nuclei-scanner',
        'timestamp': datetime.utcnow().isoformat(),
        'nuclei_installed': os.path.exists('/usr/local/bin/nuclei')
    })

@app.route('/scan', methods=['POST'])
def scan():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing required parameter: url'}), 400
        
        url = data['url']
        templates = data.get('templates', 'takeovers/')
        
        if not url.startswith(('http://', 'https://')):
            return jsonify({'error': 'Invalid URL format'}), 400
        
        result = run_nuclei_scan(url, templates)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Scan failed: {str(e)}', 'success': False}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
