from flask import Flask, request, jsonify
import sqlite3
import datetime

app = Flask(__name__)
DB = "auth.db"

# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        expiry TEXT,
        hwid TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================== ROUTES ==================

# test server
@app.route("/")
def home():
    return "Auth Server OK"

# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.json

    if not data:
        return jsonify({"status": "error", "message": "Thiếu dữ liệu"})

    user_key = data.get("key")
    hwid = data.get("hwid")

    if not user_key or not hwid:
        return jsonify({"status": "error", "message": "Thiếu key hoặc hwid"})

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT expiry, hwid FROM keys WHERE key=?", (user_key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status": "error", "message": "Key không tồn tại"})

    expiry, saved_hwid = row

    # check hết hạn
    if datetime.datetime.strptime(expiry, "%Y-%m-%d") < datetime.datetime.now():
        return jsonify({"status": "error", "message": "Key hết hạn"})

    # check HWID
    if saved_hwid:
        if saved_hwid != hwid:
            return jsonify({"status": "error", "message": "Sai HWID"})
    else:
        # lưu HWID lần đầu
        c.execute("UPDATE keys SET hwid=? WHERE key=?", (hwid, user_key))
        conn.commit()

    return jsonify({"status": "success", "message": "Login thành công"})

# CREATE KEY
@app.route("/create", methods=["POST"])
def create():
    data = request.json

    if not data:
        return jsonify({"status": "error", "message": "Thiếu dữ liệu"})

    key = data.get("key")
    days = int(data.get("days", 1))

    if not key:
        return jsonify({"status": "error", "message": "Thiếu key"})

    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("INSERT INTO keys (key, expiry, hwid) VALUES (?, ?, '')", (key, expiry))
        conn.commit()
        return jsonify({
            "status": "success",
            "key": key,
            "expiry": expiry
        })
    except:
        return jsonify({"status": "error", "message": "Key đã tồn tại"})

# CHECK KEY (tuỳ chọn)
@app.route("/check", methods=["POST"])
def check():
    data = request.json
    key = data.get("key")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT expiry FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status": "error", "message": "Key không tồn tại"})

    expiry = row[0]
    return jsonify({"status": "success", "expiry": expiry})

# ================== RUN ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)