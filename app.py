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

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/view_report/<int:report_id>")
def view_report(report_id):
    if not "username" in session:
        return redirect("/")

    param = (report_id,)
    colors          = db.query("SELECT id, name, hex FROM colors")
    tastes          = db.query("SELECT id, name, description FROM tastes")
    culinaryvalues  = db.query("SELECT id, name, description FROM culinaryvalues")
    categories      = db.query("SELECT id, name FROM categories")
    sql = """   SELECT r.*, 
                u.name AS user_name, 
                c.name AS color_name, 
                cat.name AS category_name, 
                cv.name AS culinaryvalue_name
                FROM reports r
                    JOIN users u ON r.uid = u.id
                    JOIN colors c ON r.color = c.id
                    JOIN categories cat ON r.category = cat.id
                    JOIN culinaryvalues cv ON r.culinaryvalue = cv.id
                WHERE r.id = ?"""
    fetched         = db.query(sql, param)
    return render_template("view_report.html", fetched=fetched[0], colors=colors, tastes=tastes, culvalues=culinaryvalues, categories=categories)

@app.route("/view_user/<int:user_id>")
def view_user(user_id):
    if not "username" in session:
        return redirect("/")

    param = str(user_id)
    sql_user_report_count = """ SELECT COUNT(*) FROM reports
                                WHERE reports.uid = ?
    """
    sql_user_data = """              SELECT id, name, lastlogon, credits FROM users
                                WHERE id = ?
    """

    user_report_count   = db.query(sql_user_report_count, param)[0][0]
    user_data           = db.query(sql_user_data, param)[0]
    _, user_name, lastlogon, credits = user_data
    if not lastlogon:
        lastlogon = "Never"
    return f"user_report_count {user_report_count}<br>user {user_name}, lastlogon {lastlogon}, {credits} credits"

#TODO: potential DoS surface for registered users
@app.route("/report")
def report():
    if not "username" in session:
        return redirect("/")

    colors         = db.query("SELECT id, name, hex FROM colors")
    tastes         = db.query("SELECT id, name, description FROM tastes")
    culinaryvalues = db.query("SELECT id, name, description FROM culinaryvalues")
    categories     = db.query("SELECT id, name FROM categories")
    return render_template("report.html", colors=colors, tastes=tastes, culvalues=culinaryvalues, categories=categories)

@app.route("/send_report", methods=["POST"])
def send_report():
    tastecount    = db.query("SELECT COUNT(*) FROM tastes")[0][0]
    category      = request.form["category"]
    color         = request.form["color"]
    tastes = [ i for i in range(1,int(tastecount)+1) if request.form.get(f"taste{i}") ]
    culinaryvalue = request.form["culvalue"]
    blanched      = request.form.get("blanched")
    if blanched:
        blanched = 1
    else:
        blanched = 0
    
    #TODO: validate input

    print("tastes",tastes)

    uid = get_uid(session["username"])
    sql = f"INSERT INTO reports (uid, date, category, color, culinaryvalue, blanched) VALUES (?, datetime('now'), ?, ?, ?, ?)"
    params = [uid, category, color, culinaryvalue, blanched]
    db.execute(sql, params)
    report_id = db.last_insert_id()
    print(report_id)
    sql = "INSERT INTO report_tastes (report_id, tastes_id) VALUES (?, ?)"
    for i in tastes:
        print(f"tasteassoc report_id {report_id} taste {i}")
        db.execute(sql, [report_id, i])
    return f"Report received <br> {report_id}: {params}, {tastes}"
    #TODO: redirect

@app.route("/all_reports")
def all_reports():
    sql = "SELECT * FROM reports"
    reports = db.query(sql)
    return render_template("reports.html", data=reports)

@app.route("/search", methods=["GET"])
def search():
    keywords = request.args.get("query")
    #TODO: validate input
    #TODO: multiword search how
    keywords = "%" + keywords + "%"
    sql = f"""  SELECT r.*, 
                u.name AS user_name, 
                c.name AS color_name, 
                cat.name AS category_name, 
                cv.name AS culinaryvalue_name
                FROM reports r
                    JOIN users u ON r.uid = u.id
                    JOIN colors c ON r.color = c.id
                    JOIN categories cat ON r.category = cat.id
                    JOIN culinaryvalues cv ON r.culinaryvalue = cv.id
                WHERE u.name LIKE LOWER(?)
                    OR c.name LIKE LOWER(?)
                    OR cat.name LIKE LOWER(?)
                    OR cv.name LIKE LOWER(?);"""
    result = db.query(sql, [keywords, keywords, keywords, keywords])
    print(result)
    for row in result:
        print(row)
        for item in row:
            print(item,end=", ")
        print("\n")
    return render_template("search.html", data=result)

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
