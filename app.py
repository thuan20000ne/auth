from flask import Flask, request, jsonify, render_template_string, redirect, session
import sqlite3
import datetime
import random
import string
import os

app = Flask(__name__)
app.secret_key = "secret123"
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

# ================= ADMIN =================
ADMIN_USER = "admin"
ADMIN_PASS = "123"

# ================= GEN KEY =================
def gen_key(prefix):
    return prefix + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# ================= STATS =================
def get_stats():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM keys")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM keys WHERE hwid != ''")
    used = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM keys WHERE hwid = ''")
    free = c.fetchone()[0]

    conn.close()
    return total, used, free

# ================= LOGIN PAGE =================
LOGIN = """
<body style="background:#050816;color:white;font-family:sans-serif;text-align:center;margin-top:120px;">
<h2>🔐 ADMIN LOGIN</h2>
<form method="POST">
<input name="user" placeholder="Username"><br><br>
<input name="pass" type="password" placeholder="Password"><br><br>
<button>Login</button>
</form>
</body>
"""

# ================= PANEL =================
PANEL = """
<body style="background:#050816;color:white;font-family:sans-serif;">

<h2>🌌 AUTH DASHBOARD</h2>

<a href="/logout" style="color:red;">Logout</a>

<hr>

<div>
<h3>Stats</h3>
Total: {{stats[0]}} |
Used: {{stats[1]}} |
Free: {{stats[2]}}
</div>

<hr>

<h3>Create Key</h3>
<form method="POST" action="/create">
<input name="prefix" placeholder="Prefix">
<input name="days" placeholder="Days">
<button>Create</button>
</form>

<hr>

<h3>Search</h3>
<form method="GET">
<input name="q" placeholder="Search key">
<button>Search</button>
</form>

<hr>

<table border="1" cellpadding="5">
<tr>
<th>Key</th>
<th>Expiry</th>
<th>HWID</th>
<th>Action</th>
</tr>

{% for k in keys %}
<tr>
<td>{{k[0]}}</td>
<td>{{k[1]}}</td>
<td>{{k[2]}}</td>
<td><a href="/delete?key={{k[0]}}" style="color:red;">Delete</a></td>
</tr>
{% endfor %}

</table>

</body>
"""

# ================= LOGIN WEB =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == ADMIN_USER and request.form.get("pass") == ADMIN_PASS:
            session["admin"] = True
            return redirect("/panel")

    return LOGIN

# ================= PANEL (PROTECTED) =================
@app.route("/panel")
def panel():
    if not session.get("admin"):
        return redirect("/")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    q = request.args.get("q")

    if q:
        c.execute("SELECT * FROM keys WHERE key LIKE ?", ('%'+q+'%',))
    else:
        c.execute("SELECT * FROM keys")

    keys = c.fetchall()
    conn.close()

    stats = get_stats()

    return render_template_string(PANEL, keys=keys, stats=stats)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= CREATE KEY =================
@app.route("/create", methods=["POST"])
def create():
    if not session.get("admin"):
        return redirect("/")

    prefix = request.form.get("prefix")
    days = int(request.form.get("days", 1))

    key = gen_key(prefix)
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO keys VALUES (?, ?, '')", (key, expiry))
    conn.commit()
    conn.close()

    return redirect("/panel")

# ================= DELETE KEY =================
@app.route("/delete")
def delete():
    if not session.get("admin"):
        return redirect("/")

    key = request.args.get("key")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM keys WHERE key=?", (key,))
    conn.commit()
    conn.close()

    return redirect("/panel")

# ================= API LOGIN =================
@app.route("/login", methods=["POST"])
def api_login():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT expiry, hwid FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        return {"status": "error", "msg": "Invalid key"}

    expiry, saved_hwid = row

    if datetime.datetime.strptime(expiry, "%Y-%m-%d") < datetime.datetime.now():
        return {"status": "error", "msg": "Expired"}

    if saved_hwid and saved_hwid != hwid:
        return {"status": "error", "msg": "HWID mismatch"}

    if not saved_hwid:
        c.execute("UPDATE keys SET hwid=? WHERE key=?", (hwid, key))
        conn.commit()

    conn.close()
    return {"status": "success", "msg": "Login OK"}

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    