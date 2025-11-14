import sqlite3
from flask import Flask, url_for
from flask import redirect, render_template, request, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    db.execute("INSERT INTO visits (visited_at) VALUES (datetime('now'))")
    result = db.query("SELECT COUNT(*) FROM visits")
    paragraph = "Page loaded " + str(result[0][0]) + " times"
    return render_template("index.html", visits=paragraph)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/view_report/<int:report_id>")
def view_report(report_id):
    if "user_id" not in session:
        return redirect("/")

    colors, tastes, culinaryvalues, categories = get_report_strings()
    report_tastes = get_report_taste_strings(report_id)
    fetched       = get_report_details(report_id)
    return render_template("view_report.html", fetched=fetched, colors=colors, 
                           tastes=tastes, culvalues=culinaryvalues, categories=categories, 
                           report_tastes=report_tastes)

@app.route("/view_user/<int:user_id>")
def view_user(user_id):
    if "user_id" not in session:
        return redirect("/")

    param = str(user_id)
    sql_user_report_count = """ SELECT COUNT(*) FROM reports
                                WHERE reports.uid = ?
    """
    sql_user_data = """         SELECT id, name, lastlogon, credits FROM users
                                WHERE id = ?
    """
    user_data = db.query(sql_user_data, param)
    if not user_data:
        abort(404)
    user_data = dict(user_data[0])

    if not user_data["lastlogon"]:
        user_data["lastlogon"] = "Never"

    user_report_count = db.query(sql_user_report_count, param)[0][0]

    return render_template("view_user.html", user=user_data, reports=user_report_count)

#TODO: potential DoS surface for registered users
@app.route("/create_report/")
def create_report(report_id=None):
    taste_ids = []
    if "user_id" not in session:
        return redirect("/")
    if report_id is None:
        report = None
    else:
        report = get_report_details(report_id)
        taste_ids = [ id[0] for id in get_report_tastes(report_id) ]
    colors, tastes, culinaryvalues, categories = get_report_strings()
    return render_template("create_report.html", report=report, colors=colors, tastes=tastes, 
                           culvalues=culinaryvalues, categories=categories, taste_ids=taste_ids)

@app.route("/edit_report/<int:report_id>")
def edit_report(report_id):
    require_login()
    owner_id = get_report_owner(report_id)
    require_ownership(owner_id)
    return create_report(report_id=report_id)

@app.route("/send_report_edit/<int:report_id>", methods=["POST"])
def send_report_edit(report_id):
    require_login()
    owner_id = get_report_owner(report_id)
    require_ownership(owner_id)

    category_new, color_new, culinaryvalue_new, blanched_new, tastes_new = get_reportform_contents()
    if not tastes_valid(tastes_new):
            abort(418)
    category, color, culinaryvalue, blanched, tastes = get_report_raw(report_id)
    if not (category == category_new and color == color_new and culinaryvalue == culinaryvalue_new and blanched == blanched_new):
        sql = """
            UPDATE reports SET category = ?, color = ?, culinaryvalue = ?, blanched = ?
            WHERE id = ?
        """
        db.execute(sql, [category_new, color_new, culinaryvalue_new, blanched_new, report_id])
    if not tastes == tastes_new:
        delete_tastes_sql = """
            DELETE FROM report_tastes
            WHERE report_id = ?
        """
        db.execute(delete_tastes_sql, [report_id, ])
            
        taste_sql = "INSERT INTO report_tastes (report_id, tastes_id) VALUES (?, ?);\n"
        for taste in tastes_new:
            params = [report_id, taste]
            db.execute(taste_sql, params)
    
    return redirect(url_for("view_report", report_id=report_id))


@app.route("/send_report", methods=["POST"])
def send_report():
    require_login()
    category, color, culinaryvalue, blanched, tastes = get_reportform_contents()

    uid = session["user_id"]
    sql = """   INSERT INTO reports (uid, date, category, color, culinaryvalue, blanched) 
                VALUES (?, datetime('now'), ?, ?, ?, ?)"""
    params = [uid, category, color, culinaryvalue, blanched]
    db.execute(sql, params)
    report_id = db.last_insert_id()

    sql = "INSERT INTO report_tastes (report_id, tastes_id) VALUES (?, ?)"
    tastes_inserted = 0
    for i in tastes:
        tastes_inserted += 1
        db.execute(sql, [report_id, i])
    if tastes_inserted == 0:
        db.execute(sql, [report_id, 1]) # mild

    return redirect(url_for("view_report", report_id=report_id))

@app.route("/all_reports")
def all_reports():
    sql = "SELECT * FROM reports"
    reports = db.query(sql)
    return render_template("reports.html", data=reports)

@app.route("/search", methods=["GET"])
def search():
    require_login()
    keywords = request.args.get("query")
    #TODO: validate input
    #TODO: multiword search how
    keywords = "%" + keywords + "%"
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
                WHERE u.name LIKE LOWER(?)
                    OR c.name LIKE LOWER(?)
                    OR cat.name LIKE LOWER(?)
                    OR cv.name LIKE LOWER(?);"""
    result = db.query(sql, [keywords, keywords, keywords, keywords])
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
    user_id = get_uid_from_username(username)
    session["user_id"] = user_id
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    redir    = request.form["redirect"]
    sql = "SELECT auth, id FROM users WHERE name = ?"
    password_hash, user_id = db.query(sql, [username])[0]

    if check_password_hash(password_hash, password):
        session["user_id"] = user_id
        session["username"] = username
        return redirect(redir)
    else:
        return "Wrong username or password"

@app.route("/logout")
def logout():
    del session["user_id"]
    del session["username"]
    return redirect("/")

def get_uid_from_username(username):
    sql = "SELECT id FROM users WHERE name = ?"
    return db.query(sql, [username])[0][0]

def require_login():
    if "user_id" not in session:
        abort(403)

def require_ownership(owner_id, ):
    if "user_id" not in session:
        abort(403)
    user_id = session["user_id"]
    if user_id != owner_id:
        print(f"Suspicious activity - require_ownership abort: {user_id} != {owner_id}")
        abort(403)

def get_report_strings():
    colors         = db.query("SELECT id, name, hex FROM colors")
    tastes         = db.query("SELECT id, name, description FROM tastes")
    culinaryvalues = db.query("SELECT id, name, description FROM culinaryvalues")
    categories     = db.query("SELECT id, name FROM categories")
    return (colors, tastes, culinaryvalues, categories)

def get_report_owner(report_id):
    param = (report_id, )
    sql = """ SELECT uid FROM reports WHERE reports.id = ?"""
    result = db.query(sql, param)
    if not result:
        return None
    return result[0][0]

def get_report_details(report_id):
    param = (report_id, )
    report_sql = """SELECT r.*,
                    u.name AS user_name,
                    u.id AS user_id,
                    c.name AS color_name,
                    cat.name AS category_name,
                    cv.name AS culinaryvalue_name,
                    cv.id AS culinaryvalue_id
                    FROM reports r
                        JOIN users u ON r.uid = u.id
                        JOIN colors c ON r.color = c.id
                        JOIN categories cat ON r.category = cat.id
                        JOIN culinaryvalues cv ON r.culinaryvalue = cv.id
                    WHERE r.id = ?"""
    return db.query(report_sql, param)[0]

def get_report_taste_strings(report_id):
    taste_sql =  """SELECT t.name
                    FROM tastes t
                        JOIN report_tastes rt ON t.id = rt.tastes_id
                        JOIN reports r        ON r.id = rt.report_id
                    WHERE r.id = ?"""
    param = (report_id,)
    return db.query(taste_sql, param)

def get_report_tastes(report_id):
    taste_sql =  """SELECT t.id
                    FROM tastes t
                        JOIN report_tastes rt ON t.id = rt.tastes_id
                        JOIN reports r        ON r.id = rt.report_id
                    WHERE r.id = ?"""
    param = (report_id,)
    return db.query(taste_sql, param)

def get_reportform_contents():
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
    
    return (category, color, culinaryvalue, blanched, tastes)

def get_report_raw(report_id):
    param = (report_id, )
    report_sql = """SELECT r.category, r.color, r.culinaryvalue, r.blanched
                    FROM reports r
                        JOIN users u ON r.uid = u.id
                        JOIN colors c ON r.color = c.id
                        JOIN categories cat ON r.category = cat.id
                        JOIN culinaryvalues cv ON r.culinaryvalue = cv.id
                    WHERE r.id = ?"""
    category, color, culinaryvalue, blanched = db.query(report_sql, param)[0]
    tastes = get_report_tastes(report_id)
    return (category, color, culinaryvalue, blanched, tastes)

def tastes_valid(tastes):
    return True #TODO