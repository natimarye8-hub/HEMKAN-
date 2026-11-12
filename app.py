import os
import sqlite3
import requests
from flask import Flask, jsonify, request, send_from_directory, abort

app = Flask(__name__, static_folder="static")
DB_PATH = os.environ.get("DB_PATH", "/tmp/hemkan.db")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
CHANNEL_USERNAME = os.environ.get("TELEGRAM_CHANNEL_USERNAME", "fxnux").lstrip("@")

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                message_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                photo_file_id TEXT,
                post_url TEXT,
                created_at TEXT
            )
        """)

def telegram_file_url(file_id):
    if not BOT_TOKEN or not file_id:
        return None
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
            params={"file_id": file_id}, timeout=15
        )
        r.raise_for_status()
        data = r.json()
        if data.get("ok"):
            return "/api/photo/" + data["result"]["file_path"]
    except requests.RequestException:
        pass
    return None

@app.get("/")
def home():
    return send_from_directory("static", "index.html")

@app.get("/api/movies")
def movies():
    with db() as con:
        rows = con.execute(
            "SELECT * FROM posts ORDER BY message_id DESC LIMIT 100"
        ).fetchall()
    result = []
    for row in rows:
        result.append({
            "id": row["message_id"],
            "title": row["title"],
            "description": row["description"],
            "image": telegram_file_url(row["photo_file_id"]),
            "url": row["post_url"],
            "date": row["created_at"]
        })
    return jsonify(result)

@app.get("/api/photo/<path:file_path>")
def photo(file_path):
    if not BOT_TOKEN:
        abort(503)
    try:
        r = requests.get(
            f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}",
            timeout=20
        )
        r.raise_for_status()
        from flask import Response
        return Response(r.content, content_type=r.headers.get("Content-Type", "image/jpeg"))
    except requests.RequestException:
        abort(404)

@app.post("/telegram/webhook")
def telegram_webhook():
    if WEBHOOK_SECRET:
        supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if supplied != WEBHOOK_SECRET:
            abort(403)

    update = request.get_json(silent=True) or {}
    post = update.get("channel_post") or update.get("edited_channel_post")
    if not post:
        return jsonify({"ok": True, "ignored": "not a channel post"})

    chat = post.get("chat", {})
    username = (chat.get("username") or "").lstrip("@").lower()
    if username != CHANNEL_USERNAME.lower():
        return jsonify({"ok": True, "ignored": "different channel"})

    text = post.get("text") or post.get("caption") or ""
    title = text.strip().splitlines()[0][:120] if text.strip() else "New post"
    photos = post.get("photo") or []
    photo_id = photos[-1]["file_id"] if photos else None
    message_id = post.get("message_id")
    post_url = f"https://t.me/{CHANNEL_USERNAME}/{message_id}"
    date = str(post.get("date", ""))

    with db() as con:
        con.execute("""
            INSERT OR REPLACE INTO posts
            (message_id, title, description, photo_file_id, post_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (message_id, title, text, photo_id, post_url, date))

    return jsonify({"ok": True})

@app.get("/health")
def health():
    return jsonify({"status": "ok", "channel": "@" + CHANNEL_USERNAME})

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
