"""
Enhanced Flask Frontend with WebSocket Support

This provides a full-featured chat UI with real-time updates
without requiring Node.js/npm.
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Custom Jinja2 filter to clean up text
def clean_text(text):
    """Clean up text by removing JSON artifacts and truncating at JSON markers"""
    if not text:
        return text
    # Find the first occurrence of JSON markers and truncate
    json_markers = ['","', '":"', '"sub_category"', '"description"', '{"']
    for marker in json_markers:
        if marker in text:
            text = text.split(marker)[0]
    # Clean up any trailing punctuation
    text = text.rstrip('",')
    return text.strip()

app.jinja_env.filters['clean_text'] = clean_text

# Backend API URL
BACKEND_URL = "http://localhost:8005"

@app.route('/')
def index():
    """Main chat page"""
    return render_template('chat.html')

@app.route('/funds')
def funds_page():
    """Fund browser page"""
    try:
        response = requests.get(f"{BACKEND_URL}/funds")
        funds_data = response.json()
    except:
        funds_data = {"funds": [], "total": 0}
    
    return render_template('funds.html', funds=funds_data.get('funds', []))

@app.route('/fund/<fund_name>')
def fund_detail(fund_name):
    """Individual fund detail page"""
    try:
        response = requests.get(f"{BACKEND_URL}/funds/{fund_name}")
        fund = response.json()
    except:
        fund = None
    
    return render_template('fund_detail.html', fund=fund)

@app.route('/api/chat', methods=['POST'])
def proxy_chat():
    """Proxy chat requests to backend"""
    try:
        data = request.json
        response = requests.post(f"{BACKEND_URL}/chat", json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/funds')
def proxy_funds():
    """Proxy fund requests to backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/funds", params=request.args)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/funds/search')
def proxy_search():
    """Proxy search requests to backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/funds/search", params=request.args)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to chat server'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming chat messages"""
    try:
        # Forward to backend
        response = requests.post(f"{BACKEND_URL}/chat", json={
            'message': data.get('message'),
            'session_id': data.get('session_id')
        })
        
        result = response.json()
        
        # Emit response back to client
        emit('receive_message', {
            'message': result['message'],
            'session_id': result['session_id'],
            'sources': result.get('sources', []),
            'rag_compliant': result.get('rag_compliant', True),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicators"""
    emit('typing_status', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3001, debug=True)
