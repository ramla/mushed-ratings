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

@app.route("/report")
def report():
    return render_template("report.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password = request.form["password1"]
    password2 = request.form["password2"]
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