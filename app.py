from flask import Flask, request, jsonify, render_template_string, redirect, session
import sqlite3
import datetime
import random
import string
import os

app = Flask(__name__)
app.secret_key = "thuan_secret_key"
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
ADMIN_USER = "thuan"
ADMIN_PASS = "123"

# ================= KEY =================
def gen_key(prefix):
    return prefix + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def add_time(days=0, hours=0, minutes=0):
    return datetime.datetime.now() + datetime.timedelta(days=days, hours=hours, minutes=minutes)

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

# ================= LOGIN UI =================
LOGIN = """
<body style="margin:0;overflow:hidden;font-family:sans-serif;background:black;color:white;display:flex;align-items:center;justify-content:center;height:100vh;">

<canvas id="c"></canvas>

<div style="position:absolute;background:rgba(255,255,255,0.05);padding:40px;border-radius:20px;backdrop-filter:blur(10px);text-align:center;">
<h2>🌌 THUẬN SPACE LOGIN</h2>

<form method="POST">
<input name="user" placeholder="User" style="padding:10px;width:100%;margin:5px;"><br>
<input name="pass" type="password" placeholder="Pass" style="padding:10px;width:100%;margin:5px;"><br>
<button style="width:100%;padding:10px;background:#00f0ff;border:none;">LOGIN</button>
</form>

</div>

<script>
const c = document.getElementById("c");
const ctx = c.getContext("2d");
c.width = innerWidth;
c.height = innerHeight;

let stars = [];
for(let i=0;i<150;i++){
    stars.push({x:Math.random()*c.width,y:Math.random()*c.height,r:Math.random()*2});
}

function draw(){
    ctx.clearRect(0,0,c.width,c.height);
    ctx.fillStyle="#fff";
    stars.forEach(s=>{
        ctx.beginPath();
        ctx.arc(s.x,s.y,s.r,0,Math.PI*2);
        ctx.fill();
        s.y += 1;
        if(s.y>c.height){s.y=0;s.x=Math.random()*c.width;}
    });
    requestAnimationFrame(draw);
}
draw();
</script>

</body>
"""

# ================= PANEL =================
PANEL = """
<!DOCTYPE html>
<html>
<head>
<title>Thuận SaaS Panel</title>

<style>
body{
margin:0;
font-family:sans-serif;
background:radial-gradient(circle at top,#050816,#000);
color:white;
}

.sidebar{
position:fixed;
width:240px;
height:100vh;
background:rgba(255,255,255,0.05);
backdrop-filter:blur(10px);
padding:20px;
}

.sidebar h2{color:#00f0ff;}

.sidebar a{
display:block;
color:white;
margin-top:10px;
text-decoration:none;
}

.main{
margin-left:260px;
padding:20px;
}

h1{color:#00f0ff;}

.card{
display:inline-block;
padding:15px;
margin:10px;
background:rgba(255,255,255,0.05);
border-radius:15px;
width:160px;
text-align:center;
}

input{
padding:10px;
margin:5px;
background:#111;
color:white;
border:none;
border-radius:8px;
}

button{
padding:10px;
background:linear-gradient(90deg,#00f0ff,#0066ff);
border:none;
border-radius:8px;
}

table{
width:100%;
margin-top:20px;
border-collapse:collapse;
background:rgba(255,255,255,0.03);
}

th{background:#00f0ff22;padding:10px;}
td{padding:10px;border-bottom:1px solid #222;}

</style>
</head>

<body>

<div class="sidebar">
<h2>🌌 THUẬN PANEL</h2>
<a href="/panel">Dashboard</a>
<a href="/logout">Logout</a>
</div>

<div class="main">

<h1>🚀 SPACE SAAS SYSTEM</h1>

<div class="card">TOTAL<br>{{stats[0]}}</div>
<div class="card">USED<br>{{stats[1]}}</div>
<div class="card">FREE<br>{{stats[2]}}</div>

<h3>➕ Create Key</h3>
<form method="POST" action="/create">
<input name="prefix" placeholder="Prefix">
<input name="days" placeholder="Days">
<input name="hours" placeholder="Hours">
<input name="minutes" placeholder="Minutes">
<button>Create</button>
</form>

<h3>🔑 Keys</h3>

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

<audio autoplay loop>
<source src="https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8b2f1.mp3?filename=space-ambient-110859.mp3">
</audio>

</body>
</html>
"""

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("user")==ADMIN_USER and request.form.get("pass")==ADMIN_PASS:
            session["admin"]=True
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

# ================= CREATE =================
@app.route("/create", methods=["POST"])
def create():
    if not session.get("admin"):
        return redirect("/")

    prefix = request.form.get("prefix")
    days = int(request.form.get("days") or 0)
    hours = int(request.form.get("hours") or 0)
    minutes = int(request.form.get("minutes") or 0)

    key = gen_key(prefix)
    expiry = add_time(days,hours,minutes).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO keys VALUES (?,?, '')",(key,expiry))
    conn.commit()
    conn.close()

    return redirect("/panel")

# ================= API LOGIN =================
@app.route("/login", methods=["POST"])
def api_login():
    data=request.json
    key=data.get("key")
    hwid=data.get("hwid")

    conn=sqlite3.connect(DB)
    c=conn.cursor()

    c.execute("SELECT expiry,hwid FROM keys WHERE key=?",(key,))
    row=c.fetchone()

    if not row:
        return {"status":"error"}

    expiry,saved=row

    if saved and saved!=hwid:
        return {"status":"error"}

    conn.close()
    return {"status":"success"}

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
    