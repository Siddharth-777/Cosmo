from flask import Flask, render_template, request, jsonify
from chatbot.langchain_bot import chatbot

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.form["user_input"]
    response = chatbot.run(user_input)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
