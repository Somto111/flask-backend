from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)

# Configure CORS properly for production
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])

# Telegram Configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '7456725624:AAHmNYrGKRjY34Vb9MZgHwlFn-8uMqQqlKg')
CHAT_ID = os.environ.get('CHAT_ID', '7003841804')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Store last update ID
last_update_id = 0

@app.route('/')
def home():
    """Root endpoint"""
    return jsonify({
        'status': 'online',
        'message': 'Telegram Chatbot API',
        'endpoints': {
            'send_message': '/api/send-message',
            'send_file': '/api/send-file',
            'get_messages': '/api/get-messages',
            'health': '/health'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'telegram-chatbot'})

@app.route('/api/send-message', methods=['POST', 'OPTIONS'])
def send_message():
    """Send message from chatbot to Telegram"""
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        message_text = data.get('message')
        
        if not message_text:
            return jsonify({'error': 'Message is required'}), 400
        
        print(f"Sending message: {message_text}")
        
        # Send message to Telegram
        response = requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={
                'chat_id': CHAT_ID,
                'text': message_text
            },
            timeout=10
        )
        
        result = response.json()
        print(f"Telegram response: {result}")
        
        if result.get('ok'):
            return jsonify({
                'success': True,
                'message': 'Message sent to Telegram'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('description', 'Failed to send message')
            }), 400
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Request timeout'}), 504
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send-file', methods=['POST', 'OPTIONS'])
def send_file():
    """Send file from chatbot to Telegram"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        print(f"Sending file: {file.filename}")
        
        # Send file to Telegram
        response = requests.post(
            f"{TELEGRAM_API_URL}/sendDocument",
            data={'chat_id': CHAT_ID},
            files={'document': (file.filename, file.stream, file.content_type)},
            timeout=30
        )
        
        result = response.json()
        
        if result.get('ok'):
            return jsonify({
                'success': True,
                'message': 'File sent to Telegram'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('description', 'Failed to send file')
            }), 400
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-messages', methods=['GET', 'OPTIONS'])
def get_messages():
    """Get new messages from Telegram"""
    if request.method == 'OPTIONS':
        return '', 204
    
    global last_update_id
    
    try:
        # Get updates from Telegram with shorter timeout
        response = requests.get(
            f"{TELEGRAM_API_URL}/getUpdates",
            params={
                'offset': last_update_id + 1,
                'timeout': 10  # Shorter timeout for better responsiveness
            },
            timeout=15
        )
        
        result = response.json()
        
        if not result.get('ok'):
            return jsonify({
                'success': False,
                'error': 'Failed to get updates',
                'messages': []
            }), 400
        
        new_messages = []
        updates = result.get('result', [])
        
        for update in updates:
            last_update_id = max(last_update_id, update['update_id'])
            
            message = update.get('message', {})
            
            # Handle text messages
            if 'text' in message:
                new_messages.append({
                    'type': 'text',
                    'content': message['text'],
                    'sender': message.get('from', {}).get('first_name', 'User'),
                    'timestamp': message.get('date')
                })
            
            # Handle documents/files
            elif 'document' in message:
                doc = message['document']
                new_messages.append({
                    'type': 'file',
                    'content': doc.get('file_name', 'File'),
                    'file_id': doc.get('file_id'),
                    'sender': message.get('from', {}).get('first_name', 'User'),
                    'timestamp': message.get('date')
                })
            
            # Handle photos
            elif 'photo' in message:
                photo = message['photo'][-1]
                new_messages.append({
                    'type': 'photo',
                    'content': 'Photo',
                    'file_id': photo.get('file_id'),
                    'sender': message.get('from', {}).get('first_name', 'User'),
                    'timestamp': message.get('date')
                })
        
        return jsonify({
            'success': True,
            'messages': new_messages
        })
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': True,
            'messages': []  # Return empty array on timeout
        })
    except Exception as e:
        print(f"Error getting messages: {str(e)}")
        return jsonify({
            'success': True,
            'messages': []
        })

@app.route('/api/test-telegram', methods=['GET'])
def test_telegram():
    """Test Telegram connection"""
    try:
        response = requests.get(f"{TELEGRAM_API_URL}/getMe", timeout=5)
        result = response.json()
        
        return jsonify({
            'success': result.get('ok'),
            'bot_info': result.get('result'),
            'chat_id': CHAT_ID
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/api/send-message',
            '/api/send-file',
            '/api/get-messages',
            '/api/test-telegram',
            '/health'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Delete any existing webhook before starting
    try:
        requests.post(f"{TELEGRAM_API_URL}/deleteWebhook", timeout=5)
        print("Webhook deleted successfully")
    except:
        print("Could not delete webhook")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
