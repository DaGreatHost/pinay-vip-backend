
from flask import Flask, request, jsonify
import json, os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = "data/access_codes.json"

def load_codes():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_codes(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/verify_code", methods=["POST"])
def verify_code():
    device_id = request.json.get("device_id")
    code = request.json.get("code")
    data = load_codes()
    
    if code not in data or data[code]["used"]:
        return jsonify({"status": "invalid"}), 400
    
    data[code]["used"] = True
    data[code]["used_by"] = device_id
    data[code]["used_at"] = datetime.now().isoformat()
    save_codes(data)
    return jsonify({"status": "success"})

@app.route("/generate_code", methods=["POST"])
def generate_code():
    from random import choices
    import string
    new_code = ''.join(choices(string.ascii_uppercase + string.digits, k=6))
    data = load_codes()
    data[new_code] = {"used": False}
    save_codes(data)
    return jsonify({"code": new_code})

@app.route("/fetch_posts", methods=["GET"])
def fetch_posts():
    return jsonify([
        {"type": "photo", "url": "https://example.com/photo1.jpg", "caption": "Example", "timestamp": "2025-04-13"},
        {"type": "video", "url": "https://example.com/video1.mp4", "caption": "Video sample", "timestamp": "2025-04-13"}
    ])

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

