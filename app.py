from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from chatbot.langchain_bot import run, get_chat_history  # Ensure this module exists
from datetime import datetime
import os
from vercel_python_wsgi import Vercel

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")  # Add this for sessions

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
    return render_template('new_chat.html')

@app.route("/switch_chat/<chat_id>")
def switch_chat(chat_id):
    if 'chats' in session and any(chat['id'] == chat_id for chat in session['chats']):
        session['current_chat'] = chat_id
        session.modified = True
    return redirect(url_for('index'))

@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    data = request.get_json()
    chat_id = data.get("chat_id")
    if 'chats' in session and chat_id:
        session['chats'] = [chat for chat in session['chats'] if chat['id'] != chat_id]
        if session.get('current_chat') == chat_id:
            session.pop('current_chat', None)
        session.modified = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Chat not found or session invalid"})

@app.route("/")
@app.route("/chat")
def index():
    if 'chats' not in session:
        session['chats'] = []
    current_chat = None
    if session.get('current_chat'):
        current_chat = next((chat for chat in session['chats'] if chat['id'] == session['current_chat']), None)
    return render_template(
        "index.html",
        active_page="chat",
        chats=session['chats'],
        current_chat=current_chat
    )

@app.route("/chat", methods=["POST"])
def chat():
    print("Chat route hit")
    user_input = request.form.get("user_input", "").strip()
    print(f"Received user input: {user_input}")
    if not user_input:
        print("No input provided")
        return jsonify({"text": "Please enter a message.", "audio_url": None})

    if 'chats' not in session or not session.get('current_chat'):
        print("No chat session or current chat")
        return jsonify({"text": "Please create or select a chat first.", "audio_url": None})

    current_chat = next((chat for chat in session['chats'] if chat['id'] == session['current_chat']), None)
    if not current_chat:
        print("Current chat not found")
        return jsonify({"text": "Chat not found.", "audio_url": None})

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
            "audio_url": response['audio_url'],
            "redirect": url_for('index')
        })
    except Exception as e:
        print(f"Error in chat route: {e}")
        return jsonify({"text": "An unexpected error occurred. Please try again.", "audio_url": None})

@app.route("/history")
def history():
    chat_history = get_chat_history()
    return render_template("history.html", active_page="history", chat_history=chat_history)

@app.route("/settings")
def settings():
    return render_template("settings.html", active_page="settings")

@app.route("/help")
def help():
    return render_template("help.html", active_page="help")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/notifications")
def notifications():
    notifications = [
        {"title": "Welcome!", "message": "Thanks for using Cosmo", "time": "Just now", "read": False},
        {"title": "Tip", "message": "You can use Hindi or English", "time": "2 hours ago", "read": True}
    ]
    return render_template("notifications.html", notifications=notifications)

@app.route("/update_theme", methods=["POST"])
def update_theme():
    data = request.get_json()
    theme = data.get("theme")
    if theme in ['light', 'dark']:
        session['theme'] = theme
        session.modified = True
    return jsonify({"status": "success"})

@app.route("/update_voice_language", methods=["POST"])
def update_voice_language():
    data = request.get_json()
    voice_language = data.get("voice_language")
    if voice_language in ['english', 'hindi']:
        session['voice_language'] = voice_language
        session.modified = True
    return jsonify({"status": "success"})

# Export for Vercel
app = Vercel(app)
