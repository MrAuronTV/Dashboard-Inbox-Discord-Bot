from flask import Flask, request, jsonify, render_template
from flask import send_from_directory
from werkzeug.utils import secure_filename
import requests
import json
import time
import os
import threading
import asyncio
import websockets
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)


######## CHANGE ME ########

DATA_FILE = "/PATH_TO_MESSAGES_SAVED/messages.json"
UPLOADS_PATH = "/PATH_TO_UPLOADS_SAVED//uploads"
URL_IMAGE = "http://URL_uploads/{}"
DISCORD_BOT_TOKEN = "YOUR_TOKEN_DISCORD_BOT"
DISCORD_GUILD_ID = "YOUR_DISCORD_GUILD_ID"

###########################

messages = {}
user_cache = {}
processed = set()

# -----------------------
# LOAD / SAVE
# -----------------------
def load():
    global messages
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                messages = json.load(f)
        except:
            messages = {}

def save():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

load()

def get_discord_user(user_id):

    if user_id in user_cache:
        return user_cache[user_id]["username"]

    r = requests.get(
        "https://discord.com/api/v10/users/{}".format(user_id),
        headers={"Authorization": "Bot {}".format(DISCORD_BOT_TOKEN)}
    )

    if r.status_code != 200:
        return "Unknown"

    data = r.json()

    user_cache[user_id] = data

    return data.get("username", "Unknown")

# -----------------------
# USER INFORMATIONS
# -----------------------

def get_discord_avatar(user_id):

    if user_id in user_cache:
        data = user_cache[user_id]
    else:
        r = requests.get(
            "https://discord.com/api/v10/users/{}".format(user_id),
            headers={"Authorization": "Bot {}".format(DISCORD_BOT_TOKEN)}
        )

        if r.status_code != 200:
            return "https://cdn.discordapp.com/embed/avatars/0.png"

        data = r.json()
        user_cache[user_id] = data

    avatar = data.get("avatar")

    if avatar:
        return "https://cdn.discordapp.com/avatars/{}/{}.png".format(user_id, avatar)

    return "https://cdn.discordapp.com/embed/avatars/0.png"  
    
# -----------------------
# FRONT
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search_member")
def search_member():

    query = request.args.get("q", "").lower()

    if not query:
        return jsonify([])

    r = requests.get(
        "https://discord.com/api/v10/guilds/{}/members?limit=1000".format(DISCORD_GUILD_ID),
        headers={"Authorization": "Bot {}".format(DISCORD_BOT_TOKEN)}
    )

    if r.status_code != 200:
        return jsonify([])

    members = r.json()

    result = []

    for m in members:

        user = m.get("user", {})
        username = user.get("username", "")

        if query in username.lower():

            avatar = user.get("avatar")

            if avatar:
                avatar_url = "https://cdn.discordapp.com/avatars/{}/{}.png".format(user["id"], avatar)
            else:
                avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"

            result.append({
                "id": user["id"],
                "username": username,
                "avatar": avatar_url
            })

    return jsonify(result[:10])

# -----------------------
# MESSAGE IN
# -----------------------
@app.route("/message", methods=["POST"])
def message():
    global processed
    
    data = request.json  
    user_id = str(data.get("user_id"))
    content = data.get("content", "")
    origin = data.get("origin")
    
    attachments = data.get("attachments", [])

    image = data.get("image")

    # si pas d'image directe, prendre le premier attachment
    if not image and attachments:
        image = attachments[0].get("url")

    if not content and not image:
        return jsonify({"ok": True})

    msg_id = data.get("id")
    if not msg_id:
        msg_id = "{}_{}".format(user_id, time.time())

    if msg_id in processed:
        return jsonify({"ok": True})

    processed.add(msg_id)

    username = get_discord_user(user_id)
    avatar = get_discord_avatar(user_id)

    author = "bot" if origin == "dashboard" else "user"

    msg = {
        "user_id": user_id,
        "username": username,
        "avatar": avatar,
        "author": author,
        "content": content,
        "image": image,
        "timestamp": time.time()
    }

    messages.setdefault(user_id, []).append(msg)
    save()

    if origin == "dashboard":
        send_dm_discord(int(user_id), content)

    return jsonify({"ok": True})


# -----------------------
# CONVERSATIONS
# -----------------------
@app.route("/conversations")
def conversations():
    result = []

    for uid, msgs in messages.items():
        if not msgs:
            continue

        last = None

        for m in reversed(msgs):
            if m.get("author") != "bot":
                last = m
                break

        if last is None:
            last = msgs[-1]

        result.append({
            "id": uid,
            "username": last.get("username", "Unknown"),
            "avatar": last.get("avatar", "https://cdn.discordapp.com/embed/avatars/0.png"),
            "timestamp": last.get("timestamp", 0)
        })

    return jsonify(result)


# -----------------------
# MESSAGES
# -----------------------
@app.route("/messages")
def get_messages():
    uid = request.args.get("user_id")
    return jsonify(messages.get(uid, []))

# -----------------------
# SEND DM DISCORD
# -----------------------
def send_dm_discord(user_id, content):

    r = requests.post(
        "https://discord.com/api/v10/users/@me/channels",
        headers={
            "Authorization": "Bot {}".format(DISCORD_BOT_TOKEN),
            "Content-Type": "application/json"
        },
        json={"recipient_id": user_id}
    )

    if r.status_code != 200:
        print("❌ DM ERROR:", r.text)
        return

    channel_id = r.json()["id"]

    requests.post(
        "https://discord.com/api/v10/channels/{}/messages".format(channel_id),
        headers={
            "Authorization": "Bot {}".format(DISCORD_BOT_TOKEN),
            "Content-Type": "application/json"
        },
        json={"content": content}
    ) 

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOADS_PATH, filename)

@app.route("/upload_image", methods=["POST"])
def upload_image():
    try:
        file = request.files.get("file")
        user_id = request.form.get("user_id")

        if not file or not user_id:
            return jsonify({"success": False})

        os.makedirs(UPLOADS_PATH, exist_ok=True)

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOADS_PATH, filename)
        file.save(filepath)

        image_url = URL_IMAGE.format(filename)

        # 💬 AJOUT ICI -> dashboard
        msg = {
            "user_id": user_id,
            "username": get_discord_user(user_id),
            "avatar": get_discord_avatar(user_id),
            "author": "bot",
            "content": "",
            "image": image_url,
            "timestamp": time.time()
        }

        messages.setdefault(user_id, []).append(msg)
        save()

        # 📩 DM Discord
        send_dm_discord_image_url(int(user_id), image_url)

        return jsonify({
            "success": True,
            "url": image_url
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
def send_dm_discord_image_url(user_id, url):

    r = requests.post(
        "https://discord.com/api/v10/users/@me/channels",
        headers={
            "Authorization": "Bot {}".format(DISCORD_BOT_TOKEN),
            "Content-Type": "application/json"
        },
        json={"recipient_id": user_id}
    )

    if r.status_code != 200:
        print("DM error:", r.text)
        return

    channel_id = r.json()["id"]

    # 2. download image from your NAS
    img = requests.get(url, verify=False)
    if img.status_code != 200:
        print("Image download failed")
        return

    files = {
        "files[0]": ("image.png", img.content)
    }

    r2 = requests.post(
        "https://discord.com/api/v10/channels/{}/messages".format(channel_id),
        headers={
            "Authorization": "Bot {}".format(DISCORD_BOT_TOKEN)
        },
        files=files
    )

    if r2.status_code != 200:
        print("Discord upload failed:", r2.text)

@app.route("/delete_conversation", methods=["POST"])
def delete_conversation():

    data = request.json
    user_id = str(data.get("user_id"))

    if user_id in messages:
        messages.pop(user_id, None)
        save()
        print("🗑️ Conversation supprimée:", user_id)

    return jsonify({"ok": True})
    
# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
