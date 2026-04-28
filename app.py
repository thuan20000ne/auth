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

# ================= KEY GEN =================
def gen_key(prefix):
    return prefix + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# ================= TIME CALC (PRO) =================
def add_time(minutes=0, hours=0, days=0):
    return datetime.datetime.now() + datetime.timedelta(
        minutes=minutes,
        hours=hours,
        days=days
    )

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

# ================= LOGIN PAGE (SAAS STYLE) =================
LOGIN = """
<body style="margin:0;background:black;color:white;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden;">

<div style="position:absolute;width:100%;height:100%;background:radial-gradient(circle at top,#0ff2,#000);"></div>

<div style="z-index:2;background:rgba(255,255,255,0.05);padding:40px;border-radius:20px;backdrop-filter:blur(10px);box-shadow:0 0 30px #00f0ff33;">
<h2 style="text-align:center;color:#00f0ff;">🌌 SPACE LOGIN</h2>

<form method="POST">
<input name="user" placeholder="Username" style="padding:10px;width:100%;margin:5px;"><br>
<input name="pass" type="password" placeholder="Password" style="padding:10px;width:100%;margin:5px;"><br>
<button style="width:100%;padding:10px;background:#00f0ff;border:none;border-radius:10px;">LOGIN</button>
</form>

</div>

</body>
"""

# ================= DASHBOARD SAAS =================
PANEL = """
<!DOCTYPE html>
<html>
<head>
<title>Space SaaS Panel</title>

<style>
body {
    margin:0;
    font-family: Arial;
    background: radial-gradient(circle at top, #050816, #000);
    color:white;
}

/* SPACE EFFECT */
.stars {
    position:fixed;
    width:100%;
    height:100%;
    background: radial-gradient(1px 1px at 20px 30px, #fff, transparent),
                radial-gradient(1px 1px at 120px 80px, #0ff, transparent),
                radial-gradient(1px 1px at 200px 200px, #fff, transparent);
    animation: move 80s linear infinite;
    z-index:0;
}

@keyframes move {
    from {transform:translateY(0);}
    to {transform:translateY(-2000px);}
}

/* SIDEBAR */
.sidebar {
    position:fixed;
    width:240px;
    height:100vh;
    background:rgba(10,15,40,0.7);
    backdrop-filter:blur(12px);
    padding:20px;
    z-index:2;
}

.sidebar h2 {
    color:#00f0ff;
}

.sidebar a {
    display:block;
    color:white;
    padding:10px;
    margin-top:10px;
    text-decoration:none;
}

.sidebar a:hover {
    background:#00f0ff33;
}

/* MAIN */
.main {
    margin-left:260px;
    padding:20px;
    position:relative;
    z-index:2;
}

h1 {
    color:#00f0ff;
}

/* CARD */
.card {
    display:inline-block;
    background:rgba(255,255,255,0.05);
    padding:15px;
    margin:10px;
    border-radius:14px;
    width:160px;
    text-align:center;
}

/* INPUT */
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
}

/* TABLE */
table {
    width:100%;
    margin-top:20px;
    border-collapse:collapse;
    background:rgba(255,255,255,0.03);
}

th {
    background:#00f0ff22;
    padding:10px;
}

td {
    padding:10px;
    border-bottom:1px solid #222;
}

</style>

</head>

<body>

<div class="stars"></div>

<div class="sidebar">
<h2>🌌 SAAS PANEL</h2>
<a href="/panel">Dashboard</a>
<a href="/logout">Logout</a>
</div>

<div class="main">

<h1>🚀 SPACE LICENSE SYSTEM</h1>

<div class="card">TOTAL<br>{{stats[0]}}</div>
<div class="card">USED<br>{{stats[1]}}</div>
<div class="card">FREE<br>{{stats[2]}}</div>

<h2>➕ Create Key</h2>
<form method="POST" action="/create">
<input name="prefix" placeholder="Prefix">
<input name="days" placeholder="Days">
<input name="hours" placeholder="Hours">
<input name="minutes" placeholder="Minutes">
<button>Create</button>
</form>

<h2>🔑 Keys</h2>

<table>
<tr>
<th>Key</th>
<th>Expiry</th>
<th>HWID</th>
</tr>

{% for k in keys %}
<tr>
<td>{{k[0]}}</td>
<td>{{k[1]}}</td>
<td>{{k[2]}}</td>
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
        if request.form.get("user") == ADMIN_USER and request.form.get("pass") == ADMIN_PASS:
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
    c.execute("SELECT * FROM keys")
    keys = c.fetchall()
    conn.close()

    stats = get_stats()

    return render_template_string(PANEL, keys=keys, stats=stats)

# ================= CREATE KEY (TIME PRO) =================
@app.route("/create", methods=["POST"])
def create():
    if not session.get("admin"):
        return redirect("/")

    prefix = request.form.get("prefix")
    days = int(request.form.get("days") or 0)
    hours = int(request.form.get("hours") or 0)
    minutes = int(request.form.get("minutes") or 0)

    key = gen_key(prefix)

    expiry = add_time(minutes, hours, days).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO keys VALUES (?, ?, '')", (key, expiry))
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
        return {"status":"error","msg":"Invalid key"}

    expiry, saved = row

    try:
        if datetime.datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S") < datetime.datetime.now():
            return {"status":"error","msg":"Expired"}
    except:
        return {"status":"error","msg":"Bad expiry"}

    if saved and saved != hwid:
        return {"status":"error","msg":"HWID mismatch"}

    if not saved:
        c.execute("UPDATE keys SET hwid=? WHERE key=?", (hwid, key))
        conn.commit()

    conn.close()
    return {"status":"success","msg":"OK"}

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    