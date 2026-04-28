from flask import Flask, request, jsonify, render_template_string
import sqlite3
import datetime
import random
import string
import os

app = Flask(__name__)
DB = "auth.db"

# ================= DB =================
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

# ================= GEN KEY =================
def gen_key(prefix):
    return prefix + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# ================= WEB PANEL =================
PANEL = """
<body style="background:#0f172a;color:white;font-family:sans-serif;">
<h2>🔑 KEY GENERATOR</h2>

<form method="POST" action="/create">
Prefix: <input name="prefix"><br><br>
Days: <input name="days"><br><br>
<button>Create Key</button>
</form>

<hr>

<h3>Keys</h3>
<table border="1" cellpadding="5">
<tr><th>Key</th><th>Expiry</th><th>HWID</th></tr>
{% for k in keys %}
<tr>
<td>{{k[0]}}</td>
<td>{{k[1]}}</td>
<td>{{k[2]}}</td>
</tr>
{% endfor %}
</table>
</body>
"""

@app.route("/")
def panel():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM keys")
    keys = c.fetchall()
    conn.close()
    return render_template_string(PANEL, keys=keys)

# ================= CREATE KEY =================
@app.route("/create", methods=["POST"])
def create():
    prefix = request.form.get("prefix")
    days = int(request.form.get("days", 1))

    key = gen_key(prefix)
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO keys VALUES (?, ?, '')", (key, expiry))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "key": key, "expiry": expiry})

# ================= LOGIN API =================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "error", "msg": "Missing data"})

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT expiry, hwid FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status": "error", "msg": "Invalid key"})

    expiry, saved_hwid = row

    # check expiry
    try:
        if datetime.datetime.strptime(expiry, "%Y-%m-%d") < datetime.datetime.now():
            return jsonify({"status": "error", "msg": "Expired key"})
    except:
        return jsonify({"status": "error", "msg": "Bad expiry"})

    # HWID check
    if saved_hwid and saved_hwid != hwid:
        return jsonify({"status": "error", "msg": "HWID mismatch"})

    if not saved_hwid:
        c.execute("UPDATE keys SET hwid=? WHERE key=?", (hwid, key))
        conn.commit()

    conn.close()
    return jsonify({"status": "success", "msg": "Login OK"})

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)