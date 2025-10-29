import sqlite3, db, config
from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    db.execute("INSERT INTO visits (visited_at) VALUES (datetime('now'))")
    result = db.query("SELECT COUNT(*) FROM visits")
    paragraph = "Page loaded " + str(result[0][0]) + " times"
    print(result)
    return render_template("index.html", visits=paragraph)

@app.route("/page/<int:page_id>")
def page(page_id):
    return "Tämä on sivu " + str(page_id)

@app.route("/register")
def register():
    return render_template("register.html")

#TODO: potential DoS surface for unregistered users?
@app.route("/report")
def report():
    colors         = db.query("SELECT id, name, hex FROM colors")
    tastes         = db.query("SELECT id, name, description FROM tastes")
    culinaryvalues = db.query("SELECT id, name, description FROM culinaryvalues")
    categories     = db.query("SELECT id, name FROM categories")
    return render_template("report.html", colors=colors, tastes=tastes, culvalues=culinaryvalues, categories=categories)

@app.route("/send_report", methods=["POST"])
def send_report():
    category      = request.form["category"]
    color         = request.form["color"]
    culinaryvalue = request.form["culvalue"]
    blanched      = request.form.get("blanched")
    if not blanched:
        blanched = False
    #TODO: validate input

    uid = get_uid(session["username"])
    sql = f"INSERT INTO reports (uid, date, category, color, culinaryvalue, blanched) VALUES (?, datetime('now'), ?, ?, ?, ?)"
    params = [uid, category, color, culinaryvalue, blanched]
    db.execute(sql, params)
    return f"Report received <br> {params}"

@app.route("/all_reports")
def all_reports():
    sql = "SELECT * FROM reports"
    reports = db.query(sql)
    return render_template("reports.html", data=reports)

@app.route("/create", methods=["POST"])
def create():
    username  = request.form["username"]
    password  = request.form["password1"]
    password2 = request.form["password2"]
    #TODO: validate input
    if password != password2:
        return "Passwords do not match"
    password_hash = generate_password_hash(password)

    try:
        sql = "INSERT INTO users (name, auth) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "Username already taken"

    # is this bm?
    session["username"] = username
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    redir    = request.form["redirect"]    
    sql = "SELECT auth FROM users WHERE name = ?"
    password_hash = db.query(sql, [username])[0][0]

    if check_password_hash(password_hash, password):
        session["username"] = username
        return redirect(redir)
    else:
        return "Wrong username or password"

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

def get_uid(username):
    sql = "SELECT id FROM users WHERE name = ?"
    return db.query(sql, [username])[0][0]
