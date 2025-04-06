import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime

# Assuming chatbot.langchain_bot exists; replace with actual import if different
try:
    from chatbot.langchain_bot import run, get_chat_history
except ImportError:
    # Fallback for debugging if module is missing
    def run(user_input):
        return {"text": "Mock response: " + user_input, "audio_url": None}
    def get_chat_history():
        return [{"id": "mock", "title": "Mock Chat", "messages": []}]

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")  # Secure key for sessions

class Chat:
    def __init__(self, id, title):
        self.id = id
        self.title = title
        self.messages = []
        self.created_at = datetime.now()

# Global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Global error: {e}")
    return jsonify({"text": "An internal error occurred.", "audio_url": None}), 500

@app.route("/new_chat", methods=['GET', 'POST'])
def new_chat():
    if request.method == 'POST':
        if 'chats' not in session:
            session['chats'] = []
        chat_id = str(datetime.now().timestamp())
        chat_title = request.form.get("chat_title", "").strip()
        if not chat_title:
            chat_title = f"Chat {chat_id[:8]}"
        if not any(chat['id'] == chat_id for chat in session['chats']):
            chat = Chat(chat_id, chat_title)
            session['chats'].append(vars(chat))
            session['current_chat'] = chat_id
            session.modified = True
        return redirect(url_for('index'))
    try:
        return render_template('new_chat.html')
    except Exception as e:
        print(f"Template error: {e}")
        return "Error loading new_chat.html", 500

@app.route("/switch_chat/<chat_id>")
def switch_chat(chat_id):
    if 'chats' in session and any(chat['id'] == chat_id for chat in session['chats']):
        session['current_chat'] = chat_id
        session.modified = True
    return redirect(url_for('index'))

@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    data = request.get_json() or {}
    chat_id = data.get("chat_id")
    if 'chats' in session and chat_id:
        session['chats'] = [chat for chat in session['chats'] if chat['id'] != chat_id]
        if session.get('current_chat') == chat_id:
            session.pop('current_chat', None)
        session.modified = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Chat not found or session invalid"}), 400

@app.route("/")
@app.route("/chat")
def index():
    if 'chats' not in session:
        session['chats'] = []
    current_chat = None
    if session.get('current_chat'):
        current_chat = next((chat for chat in session['chats'] if chat['id'] == session['current_chat']), None)
    try:
        return render_template(
            "index.html",
            active_page="chat",
            chats=session['chats'],
            current_chat=current_chat
        )
    except Exception as e:
        print(f"Template error: {e}")
        return "Error loading index.html", 500

@app.route("/chat", methods=["POST"])
def chat():
    print("Chat route hit")
    user_input = request.form.get("user_input", "").strip()
    print(f"Received user input: {user_input}")
    if not user_input:
        print("No input provided")
        return jsonify({"text": "Please enter a message.", "audio_url": None}), 400

    if 'chats' not in session or not session.get('current_chat'):
        print("No chat session or current chat")
        return jsonify({"text": "Please create or select a chat first.", "audio_url": None}), 400

    current_chat = next((chat for chat in session['chats'] if chat['id'] == session['current_chat']), None)
    if not current_chat:
        print("Current chat not found")
        return jsonify({"text": "Chat not found.", "audio_url": None}), 404

    try:
        response = run(user_input)
        print(f"Response from run: {response}")
        current_chat['messages'].append({
            'type': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        current_chat['messages'].append({
            'type': 'bot',
            'content': response['text'],
            'timestamp': datetime.now().isoformat()
        })
        session.modified = True
        return jsonify({
            "text": response['text'],
            "audio_url": response.get('audio_url'),  # Ensure key exists
            "redirect": url_for('index')
        })
    except Exception as e:
        print(f"Error in chat route: {e}")
        return jsonify({"text": "An unexpected error occurred. Please try again.", "audio_url": None}), 500

@app.route("/history")
def history():
    try:
        chat_history = get_chat_history()
        return render_template("history.html", active_page="history", chat_history=chat_history)
    except Exception as e:
        print(f"Template or history error: {e}")
        return "Error loading history.html", 500

@app.route("/settings")
def settings():
    try:
        return render_template("settings.html", active_page="settings")
    except Exception as e:
        print(f"Template error: {e}")
        return "Error loading settings.html", 500

@app.route("/help")
def help():
    try:
        return render_template("help.html", active_page="help")
    except Exception as e:
        print(f"Template error: {e}")
        return "Error loading help.html", 500

@app.route("/profile")
def profile():
    try:
        return render_template("profile.html")
    except Exception as e:
        print(f"Template error: {e}")
        return "Error loading profile.html", 500

@app.route("/notifications")
def notifications():
    notifications = [
        {"title": "Welcome!", "message": "Thanks for using Cosmo", "time": "Just now", "read": False},
        {"title": "Tip", "message": "You can use Hindi or English", "time": "2 hours ago", "read": True}
    ]
    try:
        return render_template("notifications.html", notifications=notifications)
    except Exception as e:
        print(f"Template error: {e}")
        return "Error loading notifications.html", 500

@app.route("/update_theme", methods=["POST"])
def update_theme():
    data = request.get_json() or {}
    theme = data.get("theme")
    if theme in ['light', 'dark']:
        session['theme'] = theme
        session.modified = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid theme"}), 400

@app.route("/update_voice_language", methods=["POST"])
def update_voice_language():
    data = request.get_json() or {}
    voice_language = data.get("voice_language")
    if voice_language in ['english', 'hindi']:
        session['voice_language'] = voice_language
        session.modified = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid language"}), 400

# For Vercel serverless compatibility (no if __name__ block needed)
from vercel_python_wsgi import Vercel
app = Vercel(app)
