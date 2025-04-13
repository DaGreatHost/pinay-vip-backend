from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os
from datetime import datetime
import asyncio

from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo

app = Flask(__name__)
CORS(app)

DATA_FILE = "data/access_codes.json"

# Ensure data directory and file exist
if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_codes():
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
    print("✅ /generate_code called")
    from random import choices
    import string
    new_code = ''.join(choices(string.ascii_uppercase + string.digits, k=6))
    data = load_codes()
    data[new_code] = {"used": False}
    save_codes(data)
    return jsonify({"code": new_code})

@app.route("/access_codes.json", methods=["GET"])
def get_codes():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify({"error": "Could not load codes"}), 500

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
                        "timestamp": str(msg.date.date())
                    })

    return jsonify(posts)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
