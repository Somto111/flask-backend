# import hashlib
# import os
# from flask import Flask, request, jsonify, render_template, flash, url_for
# from dotenv import load_dotenv
# import mailchimp_marketing as MailchimpMarketing
# from mailchimp_marketing.api_client import ApiClientError
# from unicodedata import category
# from werkzeug.utils import redirect
# import requests
# from flask_cors import CORS
# import time
# import threading

# from flask_mail import Mail, Message



# # Flask-Mail config


# load_dotenv()

# app = Flask(__name__)

# # Add this to your Flask app for better CORS support
# CORS(app, resources={
#     r"/*": {
#         "origins": ["https://your-netlify-site.netlify.app", "http://localhost:*"],
#         "methods": ["GET", "POST", "OPTIONS"],
#         "allow_headers": ["Content-Type"]
#     }
# })
# app.secret_key = "mysupersecretkey123"

# MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
# MAILCHIMP_SERVER_PREFIX = os.getenv("MAILCHIMP_SERVER_PREFIX")
# MAILCHIMP_LIST_ID =  os.getenv("MAILCHIMP_LIST_ID")
# TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# CHAT_ID = os.getenv("CHAT_ID")


# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")   # your Gmail
# app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")

# mail=Mail(app)

# client = MailchimpMarketing.Client()
# client.set_config({
#     "api_key": MAILCHIMP_API_KEY,
#     "server": MAILCHIMP_SERVER_PREFIX
# })


# # Store messages in memory
# messages = []
# last_processed_update_id = None
# message_queue = []  # Queue for new responses

# @app.route('/')
# def home():
#     return render_template("index.html")

# @app.route('/send_message', methods=['POST'])
# def send_message():
#     """Send message to Telegram"""
#     data = request.json
#     user_message = data.get("message")

#     if not user_message:
#         return jsonify({"error": "No message provided"}), 400

#     # Clear the message queue before sending a new message
#     global message_queue
#     message_queue = []

#     # Send to Telegram
#     url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
#     payload = {
#         "chat_id": CHAT_ID,
#         "text": user_message
#     }

#     try:
#         response = requests.post(url, json=payload)
#         telegram_data = response.json()

#         if response.status_code == 200 and telegram_data.get("ok"):
#             print(f"✅ Sent to Telegram: {user_message}")
#             return jsonify({
#                 "status": "Message sent successfully",
#                 "success": True
#             }), 200
#         else:
#             return jsonify({
#                 "status": "Failed to send message",
#                 "error": telegram_data.get("description", "Unknown error"),
#                 "success": False
#             }), 500

#     except Exception as e:
#         print(f"❌ Error: {e}")
#         return jsonify({
#             "status": "Error sending message",
#             "error": str(e),
#             "success": False
#         }), 500


# @app.route('/get_response', methods=['GET'])
# def get_response():
#     try:
#         if message_queue:
#             # Pop the first message from queue
#             response_msg = message_queue.pop(0)
#             print(f"📤 Sending response to web: {response_msg['text']}")
#             return jsonify({
#                 "response": response_msg['text'],
#                 "success": True,
#                 "timestamp": response_msg['timestamp']
#             }), 200
#         return jsonify({
#             "response": None,
#             "success": False
#         }), 200
#     except Exception as e:
#         return jsonify({
#             "response": None,
#             "success": False,
#             "error": str(e)
#         }), 200


# @app.route('/get_all_messages', methods=['GET'])
# def get_all_messages():
#     return jsonify({
#         "messages": messages,
#         "count": len(messages)
#     })


# @app.route('/clear_messages', methods=['POST'])
# def clear_messages():
#     global messages
#     messages = []
#     return jsonify({"status": "Messages cleared"})


# @app.errorhandler(404)
# def not_found(e):
#     return jsonify({"error": "Endpoint not found"}), 404


# @app.errorhandler(500)
# def server_error(e):
#     return jsonify({"error": "Internal server error"}), 500


# # Polling function to get updates from Telegram
# def poll_telegram_updates():
#     global last_processed_update_id, message_queue
#     print("🔄 Starting Telegram polling...")
#     offset = None

#     while True:
#         try:
#             url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
#             params = {
#                 "timeout": 30,
#                 "offset": offset
#             }

#             response = requests.get(url, params=params, timeout=35)
#             data = response.json()

#             if data.get("ok"):
#                 updates = data.get("result", [])

#                 for update in updates:
#                     offset = update["update_id"] + 1

#                     if "message" in update:
#                         message = update['message']
#                         chat_id = str(message['chat']['id'])
#                         text = message.get('text', '')
#                         message_id = message.get('message_id')

#                         # Check if message is from the bot itself
#                         from_user = message.get('from', {})
#                         is_bot = from_user.get('is_bot', False)

#                         # Only process messages from your chat that are NOT from the bot
#                         if chat_id == CHAT_ID and not is_bot:
#                             # Avoid processing the same message twice
#                             if last_processed_update_id != message_id:
#                                 msg_obj = {
#                                     'text': text,
#                                     'timestamp': time.time(),
#                                     'message_id': message_id
#                                 }
#                                 messages.append(msg_obj)
#                                 message_queue.append(msg_obj)  # Add to queue
#                                 last_processed_update_id = message_id
#                                 print(f"📨 New message from Telegram user: {text}")
#                                 print(f"📊 Queue size: {len(message_queue)}")
#                             else:
#                                 print(f"⏭️ Skipping duplicate message: {message_id}")
#                         elif is_bot:
#                             print(f"🤖 Ignoring bot's own message: {text}")

#         except Exception as e:
#             print(f"❌ Polling error: {e}")
#             time.sleep(5)

# @app.route('/join_waitlist', methods=['GET','POST'])
# def join_waitlist():
#     if request.method =='GET':
#         return "waitlist endpoint is available"

#     email = request.form.get('email')

#     if not email or '@' not in email:
#         flash("please enter a valid email.", "error")
#         return redirect(url_for('home'))
#     try:
#        response= client.lists.add_list_member(MAILCHIMP_LIST_ID,{
#            "email_address": email,
#            "status": "subscribed"
#        })

#        flash("You are on the waitlist!", "success")
#        return redirect(url_for('home'))
#     except ApiClientError as error:
#         error_msg = str("you have been registered")

#         if "Member Exists" in error_msg:
#             subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
#             client.lists.set_list_member(MAILCHIMP_LIST_ID, subscriber_hash,{
#                 "email_address": email,
#                 "status_if_new": "subscribed",
#                 "status": "subscribed"
#             })
#             flash("You are already on the waitlist!", 'info')
#             return redirect(url_for('home'))

#         flash( error_msg, "error")
#         return redirect(url_for('home'))



# if __name__ == '__main__':
#     print("🚀 Starting Flask app with Telegram polling...")
#     print(f"📱 Monitoring Telegram chat: {CHAT_ID}")

#     # Start polling in background thread
#     polling_thread = threading.Thread(target=poll_telegram_updates, daemon=True)
#     polling_thread.start()

#     # app.run(debug=True, port=5000, use_reloader=False)
    
#     app.run()






# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import requests
# import threading
# import time

# app = Flask(__name__)
# CORS(app)  # Enable CORS for frontend-backend communication

# # Telegram Configuration
# TELEGRAM_TOKEN = "7456725624:AAHmNYrGKRjY34Vb9MZgHwlFn-8uMqQqlKg"
# CHAT_ID = "7003841804"
# TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# # Store messages in memory (use database in production)
# messages = []
# last_update_id = 0

# @app.route('/api/send-message', methods=['POST'])
# def send_message():
#     """Send message from chatbot to Telegram"""
#     try:
#         data = request.json
#         message_text = data.get('message')
        
#         if not message_text:
#             return jsonify({'error': 'Message is required'}), 400
        
#         # Send message to Telegram
#         response = requests.post(
#             f"{TELEGRAM_API_URL}/sendMessage",
#             json={
#                 'chat_id': CHAT_ID,
#                 'text': message_text
#             }
#         )
        
#         result = response.json()
        
#         if result.get('ok'):
#             return jsonify({
#                 'success': True,
#                 'message': 'Message sent to Telegram'
#             })
#         else:
#             return jsonify({
#                 'error': result.get('description', 'Failed to send message')
#             }), 400
            
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/send-file', methods=['POST'])
# def send_file():
#     """Send file from chatbot to Telegram"""
#     try:
#         if 'file' not in request.files:
#             return jsonify({'error': 'No file provided'}), 400
        
#         file = request.files['file']
        
#         # Send file to Telegram
#         response = requests.post(
#             f"{TELEGRAM_API_URL}/sendDocument",
#             data={'chat_id': CHAT_ID},
#             files={'document': (file.filename, file.stream, file.content_type)}
#         )
        
#         result = response.json()
        
#         if result.get('ok'):
#             return jsonify({
#                 'success': True,
#                 'message': 'File sent to Telegram'
#             })
#         else:
#             return jsonify({
#                 'error': result.get('description', 'Failed to send file')
#             }), 400
            
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/get-messages', methods=['GET'])
# def get_messages():
#     """Get new messages from Telegram"""
#     global last_update_id
    
#     try:
#         # Get updates from Telegram
#         response = requests.get(
#             f"{TELEGRAM_API_URL}/getUpdates",
#             params={
#                 'offset': last_update_id + 1,
#                 'timeout': 30
#             }
#         )
        
#         result = response.json()
        
#         if not result.get('ok'):
#             return jsonify({'error': 'Failed to get updates'}), 400
        
#         new_messages = []
#         updates = result.get('result', [])
        
#         for update in updates:
#             last_update_id = max(last_update_id, update['update_id'])
            
#             message = update.get('message', {})
            
#             # Handle text messages
#             if 'text' in message:
#                 new_messages.append({
#                     'type': 'text',
#                     'content': message['text'],
#                     'sender': message.get('from', {}).get('first_name', 'User'),
#                     'timestamp': message.get('date')
#                 })
            
#             # Handle documents/files
#             elif 'document' in message:
#                 doc = message['document']
#                 new_messages.append({
#                     'type': 'file',
#                     'content': doc.get('file_name', 'File'),
#                     'file_id': doc.get('file_id'),
#                     'sender': message.get('from', {}).get('first_name', 'User'),
#                     'timestamp': message.get('date')
#                 })
            
#             # Handle photos
#             elif 'photo' in message:
#                 photo = message['photo'][-1]  # Get largest photo
#                 new_messages.append({
#                     'type': 'photo',
#                     'content': 'Photo',
#                     'file_id': photo.get('file_id'),
#                     'sender': message.get('from', {}).get('first_name', 'User'),
#                     'timestamp': message.get('date')
#                 })
        
#         return jsonify({
#             'success': True,
#             'messages': new_messages
#         })
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/get-file', methods=['GET'])
# def get_file():
#     """Get file from Telegram"""
#     try:
#         file_id = request.args.get('file_id')
        
#         if not file_id:
#             return jsonify({'error': 'file_id is required'}), 400
        
#         # Get file path
#         response = requests.get(
#             f"{TELEGRAM_API_URL}/getFile",
#             params={'file_id': file_id}
#         )
        
#         result = response.json()
        
#         if result.get('ok'):
#             file_path = result['result']['file_path']
#             file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            
#             return jsonify({
#                 'success': True,
#                 'file_url': file_url
#             })
#         else:
#             return jsonify({
#                 'error': result.get('description', 'Failed to get file')
#             }), 400
            
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/webhook', methods=['POST'])
# def webhook():
#     """Webhook endpoint for Telegram updates (alternative to polling)"""
#     try:
#         update = request.json
        
#         # Process the update
#         message = update.get('message', {})
        
#         if 'text' in message:
#             # Store or process the message
#             messages.append({
#                 'type': 'text',
#                 'content': message['text'],
#                 'sender': message.get('from', {}).get('first_name', 'User'),
#                 'timestamp': message.get('date')
#             })
        
#         return jsonify({'success': True})
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/set-webhook', methods=['POST'])
# def set_webhook():
#     """Set webhook URL for Telegram"""
#     try:
#         data = request.json
#         webhook_url = data.get('url')
        
#         if not webhook_url:
#             return jsonify({'error': 'Webhook URL is required'}), 400
        
#         response = requests.post(
#             f"{TELEGRAM_API_URL}/setWebhook",
#             json={'url': webhook_url}
#         )
        
#         result = response.json()
        
#         if result.get('ok'):
#             return jsonify({
#                 'success': True,
#                 'message': 'Webhook set successfully'
#             })
#         else:
#             return jsonify({
#                 'error': result.get('description', 'Failed to set webhook')
#             }), 400
            
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/delete-webhook', methods=['POST'])
# def delete_webhook():
#     """Delete webhook (use polling instead)"""
#     try:
#         response = requests.post(f"{TELEGRAM_API_URL}/deleteWebhook")
#         result = response.json()
        
#         if result.get('ok'):
#             return jsonify({
#                 'success': True,
#                 'message': 'Webhook deleted successfully'
#             })
#         else:
#             return jsonify({
#                 'error': result.get('description', 'Failed to delete webhook')
#             }), 400
            
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/health', methods=['GET'])
# def health():
#     """Health check endpoint"""
#     return jsonify({'status': 'healthy'})

# if __name__ == '__main__':
#     # Delete any existing webhook before starting
#     requests.post(f"{TELEGRAM_API_URL}/deleteWebhook")
    
#     # Run Flask app
#     app.run(debug=True, host='0.0.0.0', port=5000)



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
