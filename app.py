import hashlib
import os
from flask import Flask, request, jsonify, render_template, flash, url_for
from dotenv import load_dotenv
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from unicodedata import category
from werkzeug.utils import redirect
import requests
from flask_cors import CORS
import time
import threading

from flask_mail import Mail, Message



# Flask-Mail config


load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = "mysupersecretkey123"

MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
MAILCHIMP_SERVER_PREFIX = os.getenv("MAILCHIMP_SERVER_PREFIX")
MAILCHIMP_LIST_ID =  os.getenv("MAILCHIMP_LIST_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")   # your Gmail
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")

mail=Mail(app)

client = MailchimpMarketing.Client()
client.set_config({
    "api_key": MAILCHIMP_API_KEY,
    "server": MAILCHIMP_SERVER_PREFIX
})


# Store messages in memory
messages = []
last_processed_update_id = None
message_queue = []  # Queue for new responses

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/send_message', methods=['POST'])
def send_message():
    """Send message to Telegram"""
    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Clear the message queue before sending a new message
    global message_queue
    message_queue = []

    # Send to Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": user_message
    }

    try:
        response = requests.post(url, json=payload)
        telegram_data = response.json()

        if response.status_code == 200 and telegram_data.get("ok"):
            print(f"✅ Sent to Telegram: {user_message}")
            return jsonify({
                "status": "Message sent successfully",
                "success": True
            }), 200
        else:
            return jsonify({
                "status": "Failed to send message",
                "error": telegram_data.get("description", "Unknown error"),
                "success": False
            }), 500

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            "status": "Error sending message",
            "error": str(e),
            "success": False
        }), 500


@app.route('/get_response', methods=['GET'])
def get_response():
    try:
        if message_queue:
            # Pop the first message from queue
            response_msg = message_queue.pop(0)
            print(f"📤 Sending response to web: {response_msg['text']}")
            return jsonify({
                "response": response_msg['text'],
                "success": True,
                "timestamp": response_msg['timestamp']
            }), 200
        return jsonify({
            "response": None,
            "success": False
        }), 200
    except Exception as e:
        return jsonify({
            "response": None,
            "success": False,
            "error": str(e)
        }), 200


@app.route('/get_all_messages', methods=['GET'])
def get_all_messages():
    return jsonify({
        "messages": messages,
        "count": len(messages)
    })


@app.route('/clear_messages', methods=['POST'])
def clear_messages():
    global messages
    messages = []
    return jsonify({"status": "Messages cleared"})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# Polling function to get updates from Telegram
def poll_telegram_updates():
    global last_processed_update_id, message_queue
    print("🔄 Starting Telegram polling...")
    offset = None

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {
                "timeout": 30,
                "offset": offset
            }

            response = requests.get(url, params=params, timeout=35)
            data = response.json()

            if data.get("ok"):
                updates = data.get("result", [])

                for update in updates:
                    offset = update["update_id"] + 1

                    if "message" in update:
                        message = update['message']
                        chat_id = str(message['chat']['id'])
                        text = message.get('text', '')
                        message_id = message.get('message_id')

                        # Check if message is from the bot itself
                        from_user = message.get('from', {})
                        is_bot = from_user.get('is_bot', False)

                        # Only process messages from your chat that are NOT from the bot
                        if chat_id == CHAT_ID and not is_bot:
                            # Avoid processing the same message twice
                            if last_processed_update_id != message_id:
                                msg_obj = {
                                    'text': text,
                                    'timestamp': time.time(),
                                    'message_id': message_id
                                }
                                messages.append(msg_obj)
                                message_queue.append(msg_obj)  # Add to queue
                                last_processed_update_id = message_id
                                print(f"📨 New message from Telegram user: {text}")
                                print(f"📊 Queue size: {len(message_queue)}")
                            else:
                                print(f"⏭️ Skipping duplicate message: {message_id}")
                        elif is_bot:
                            print(f"🤖 Ignoring bot's own message: {text}")

        except Exception as e:
            print(f"❌ Polling error: {e}")
            time.sleep(5)

@app.route('/join_waitlist', methods=['GET','POST'])
def join_waitlist():
    if request.method =='GET':
        return "waitlist endpoint is available"

    email = request.form.get('email')

    if not email or '@' not in email:
        flash("please enter a valid email.", "error")
        return redirect(url_for('home'))
    try:
       response= client.lists.add_list_member(MAILCHIMP_LIST_ID,{
           "email_address": email,
           "status": "subscribed"
       })

       flash("You are on the waitlist!", "success")
       return redirect(url_for('home'))
    except ApiClientError as error:
        error_msg = str("you have been registered")

        if "Member Exists" in error_msg:
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
            client.lists.set_list_member(MAILCHIMP_LIST_ID, subscriber_hash,{
                "email_address": email,
                "status_if_new": "subscribed",
                "status": "subscribed"
            })
            flash("You are already on the waitlist!", 'info')
            return redirect(url_for('home'))

        flash( error_msg, "error")
        return redirect(url_for('home'))



if __name__ == '__main__':
    print("🚀 Starting Flask app with Telegram polling...")
    print(f"📱 Monitoring Telegram chat: {CHAT_ID}")

    # Start polling in background thread
    polling_thread = threading.Thread(target=poll_telegram_updates, daemon=True)
    polling_thread.start()

    # app.run(debug=True, port=5000, use_reloader=False)
    
    app.run()
