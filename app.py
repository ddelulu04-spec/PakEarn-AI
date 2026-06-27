from flask import Flask, render_template, request, jsonify, session
from duckduckgo_search import DDGS
from groq import Groq
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = "pakearn_secret_2026"

MEMORY_FILE = "pakearn_memory.json"
from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---- MEMORY ----
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---- WEB SEARCH ----
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            output = ""
            for r in results:
                output += f"Title: {r['title']}\n"
                output += f"Summary: {r['body']}\n\n"
            return output if output else "No results found"
    except Exception as e:
        return f"Search failed: {str(e)}"

def get_system_prompt(user_data):
    return f"""
You are PakEarn AI — a smart online earning guide specifically for Pakistani students.

Your job is to:
1. Ask about the user's skills, interests, and available time
2. Suggest the best online earning platforms suitable for Pakistan
3. Give realistic earning estimates in PKR and USD
4. Provide step-by-step guidance to get started
5. Answer questions about freelancing, YouTube, Fiverr, Upwork, remote jobs

Platforms you know about for Pakistan:
- Fiverr (freelancing — logo, writing, coding, video editing)
- Upwork (freelancing — development, design, writing)
- YouTube (content creation — monetization after 1000 subscribers)
- Toptal (elite freelancing — high paying)
- PeoplePerHour (freelancing)
- Remote job boards (LinkedIn, Indeed, RemoteOK)
- Teaching online (Preply, iTalki for language teaching)
- Selling digital products (Gumroad, Etsy)

Important Pakistan-specific info:
- Payoneer and Wise work well for receiving payments
- Freelancing income is tax-free up to certain limits in Pakistan
- Internet speed can be an issue — suggest accordingly
- Always give earning estimates in both PKR and USD

Current date: {datetime.now().strftime("%Y-%m-%d")}
User profile so far: {json.dumps(user_data) if user_data else "New user — ask about their skills first"}

Be friendly, motivating, and realistic. Never give fake earning promises.
Always respond in simple clear English.
Format your responses clearly using short paragraphs.
"""

@app.route("/")
def home():
    user_data = load_memory()
    user_name = user_data.get("name", None)
    return render_template("index.html", user_name=user_name)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"reply": "Please type something!"})

    user_data = load_memory()

    # Initialize conversation in session
    if "messages" not in session:
        session["messages"] = [
            {"role": "system", "content": get_system_prompt(user_data)}
        ]

    full_message = user_input
    searched = False

    # Save name if mentioned
    if "my name is" in user_input.lower():
        name = user_input.lower().replace("my name is", "").strip().title()
        user_data["name"] = name
        save_memory(user_data)

    # Save skills if mentioned
    if "i know" in user_input.lower() or "my skill" in user_input.lower():
        user_data["skills_mentioned"] = user_input
        save_memory(user_data)

    # Search web for current info
    if any(word in user_input.lower() for word in
           ["fiverr", "upwork", "youtube", "earning",
            "freelance", "how to start", "latest"]):
        search_results = search_web(user_input + " Pakistan 2026")
        full_message += f"\n\nLatest web info:\n{search_results}"
        searched = True

    session["messages"].append({"role": "user", "content": full_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=session["messages"],
        max_tokens=1000
    )

    ai_reply = response.choices[0].message.content
    session["messages"].append({"role": "assistant", "content": ai_reply})
    session.modified = True

    return jsonify({
        "reply": ai_reply,
        "searched": searched,
        "user_name": user_data.get("name", None)
    })

@app.route("/profile")
def profile():
    user_data = load_memory()
    return jsonify(user_data)

@app.route("/clear")
def clear():
    session.clear()
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    app.run(debug=True)