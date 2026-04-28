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
<!DOCTYPE html>
<html>
<head>
<title>Pro Panel</title>
<style>
body {
    margin:0;
    font-family: Arial;
    background: radial-gradient(circle at top, #050816, #000);
    color:white;
}

.sidebar {
    position:fixed;
    width:220px;
    height:100vh;
    background:rgba(10,15,40,0.85);
    padding:20px;
}

.sidebar h2 {color:#00f0ff;}

.sidebar a {
    display:block;
    color:white;
    padding:10px;
    margin-top:10px;
    text-decoration:none;
}

.sidebar a:hover {background:#00f0ff33;}

.main {
    margin-left:240px;
    padding:20px;
}

h1 {color:#00f0ff;}

.card {
    display:inline-block;
    background:rgba(255,255,255,0.05);
    padding:15px;
    margin:10px;
    border-radius:12px;
    width:160px;
    text-align:center;
}

input {
    padding:10px;
    margin:5px;
    border:none;
    border-radius:8px;
    background:#111827;
    color:white;
}

button {
    padding:10px 15px;
    background:linear-gradient(90deg,#00f0ff,#0066ff);
    border:none;
    border-radius:8px;
    cursor:pointer;
    font-weight:bold;
}

table {
    width:100%;
    margin-top:20px;
    border-collapse:collapse;
    background:rgba(255,255,255,0.03);
}

th {background:#00f0ff22;padding:10px;}
td {padding:10px;border-bottom:1px solid #222;}

.delete {color:red;}
</style>
</head>

<body>

<div class="sidebar">
<h2>🌌 ADMIN</h2>
<a href="/panel">Dashboard</a>
<a href="/logout">Logout</a>
</div>

<div class="main">

<h1>🚀 PRO AUTH SYSTEM</h1>

<div class="card">TOTAL<br>{{stats[0]}}</div>
<div class="card">USED<br>{{stats[1]}}</div>
<div class="card">FREE<br>{{stats[2]}}</div>

<h2>➕ Create Key</h2>
<form method="POST" action="/create">
<input name="prefix" placeholder="Prefix (VIP/PRO)">
<input name="days" placeholder="Days">
<button>Create</button>
</form>

<h2>🔍 Search</h2>
<form method="GET">
<input name="q" placeholder="Search key">
<button>Search</button>
</form>

<h2>🔑 Keys</h2>

<table>
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
<td><a class="delete" href="/delete?key={{k[0]}}">DELETE</a></td>
</tr>
{% endfor %}

</table>

</div>

</body>
</html>
"""

# ================= LOGIN WEB =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == ADMIN_USER and request.form["pass"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/panel")
    return LOGIN

# ================= PANEL =================
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
    