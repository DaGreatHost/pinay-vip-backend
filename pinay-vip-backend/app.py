from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os, json, asyncio, string, logging
from random import choices

from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo

# Flask app setup
app = Flask(__name__)
CORS(app, origins=["https://tgreward.shop"], supports_credentials=True)

# Logging for Railway logs
logging.basicConfig(level=logging.INFO)

DATA_FILE = "data/access_codes.json"

# Ensure data folder and JSON file exist
os.makedirs("data", exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# Helper functions
def load_codes():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_codes(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# API endpoint to verify a code
@app.route("/verify_code", methods=["POST"])
def verify_code():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "Missing JSON body"}), 400

    device_id = payload.get("device_id")
    code = payload.get("code")

    if not device_id or not code:
        return jsonify({"error": "Missing 'device_id' or 'code'"}), 400

    data = load_codes()
    if code not in data or data[code]["used"]:
        return jsonify({"status": "invalid"}), 400

    data[code]["used"] = True
    data[code]["used_by"] = device_id
    data[code]["used_at"] = datetime.now().isoformat()
    save_codes(data)

    return jsonify({"status": "success"})

# Generate a new 6-character access code
@app.route("/generate_code", methods=["POST"])
def generate_code():
    try:
        new_code = ''.join(choices(string.ascii_uppercase + string.digits, k=6))
        data = load_codes()
        data[new_code] = {"used": False}
        save_codes(data)
        app.logger.info(f"✅ New code generated: {new_code}")
        return jsonify({"code": new_code})
    except Exception as e:
        app.logger.error(f"❌ Error generating code: {str(e)}")
        return jsonify({"error": f"Failed to generate code: {str(e)}"}), 500

# Endpoint to return all access codes
@app.route("/access_codes.json", methods=["GET"])
def get_codes():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Could not load codes: {str(e)}"}), 500

# Fetch latest posts from a Telegram channel
@app.route("/fetch_posts", methods=["GET"])
def fetch_posts():
    return asyncio.run(get_telegram_posts())

async def get_telegram_posts():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_HASH")
    channel = os.getenv("CHANNEL")

    posts = []

    async with TelegramClient("session", api_id, api_hash) as client:
        async for msg in client.iter_messages(channel, limit=10):
            if msg.media:
                media_type = None
                if isinstance(msg.media, MessageMediaPhoto):
                    media_type = "photo"
                elif isinstance(msg.media, MessageMediaDocument):
                    for attr in msg.media.document.attributes:
                        if isinstance(attr, DocumentAttributeVideo):
                            media_type = "video"

                if media_type:
                    posts.append({
                        "type": media_type,
                        "url": f"https://t.me/{channel.strip('@')}/{msg.id}",
                        "caption": msg.text or "",
                        "timestamp": str(msg.date)
                    })

    return jsonify(posts)

# Main
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
