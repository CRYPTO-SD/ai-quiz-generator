import os
import json
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import sys
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

sys.stdout.reconfigure(encoding='utf-8')

# Load API key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not found in .env file. The API will not work.")

app = Flask(__name__, static_folder="static", template_folder="templates")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory(app.static_folder, filename)

def check_api_key():
    if not GEMINI_API_KEY:
        return {"error": "API key is missing. Please set the GEMINI_API_KEY environment variable."}
    
    test_prompt = "Say 'Hello' in a JSON response."
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {"contents": [{"parts": [{"text": test_prompt}]}]}

    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)
    
    if response.status_code == 200:
        return {"success": "API key is valid."}
    else:
        return {"error": f"Invalid API key. Status Code: {response.status_code}", "details": response.text}

def generate_quiz(topic, difficulty, num_questions, question_type):
    if not GEMINI_API_KEY:
        return {"error": "API key is missing. Please set the GEMINI_API_KEY environment variable."}

    prompt = f"Generate {num_questions} {question_type} quiz questions on {topic} with {difficulty} difficulty. Return JSON array of questions with 'question', 'options', and 'answer' fields."
    logging.debug("Generated Prompt: %s", prompt)

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)
        logging.debug("Response Status Code: %s", response.status_code)
        logging.debug("Response Text: %s", response.text)

        if response.status_code == 200:
            result = response.json()
            raw_text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            cleaned_text = raw_text.strip().strip("```json").strip("```").strip()
            return {"quiz": json.loads(cleaned_text)}
        else:
            logging.error("API Error %s: %s", response.status_code, response.text)
            return {"error": "Failed to generate quiz", "details": response.text}
    except Exception as e:
        logging.error("Request Error: %s", str(e))
        return {"error": "An unexpected error occurred", "details": str(e)}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/quiz")
def quiz_page():
    return render_template("quiz.html")

@app.route("/check_api", methods=["GET"])
def check_api():
    return jsonify(check_api_key())

@app.route("/generate_quiz", methods=["POST"])
def generate_quiz_api():
    try:
        data = request.get_json()
        logging.debug("Request Data: %s", data)

        topic = data.get("topic", "General Knowledge")
        difficulty = data.get("difficulty", "Medium")
        num_questions = int(data.get("num_questions", 5))
        question_type = data.get("question_type", "multiple_choice")

        quiz = generate_quiz(topic, difficulty, num_questions, question_type)
        logging.debug("Generated Quiz: %s", quiz)

        return jsonify(quiz)
    except Exception as e:
        logging.error("Error in /generate_quiz: %s", str(e))
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logging.debug("Flask app is running on http://127.0.0.1:5000")
    logging.debug("Routes: %s", app.url_map)
    app.run(host="0.0.0.0", port=port, debug=True)
