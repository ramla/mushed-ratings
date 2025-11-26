import sqlite3
from flask import Flask, url_for
from flask import redirect, render_template, request, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import db
import config
import query

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/view_report/<int:report_id>")
def view_report(report_id):
    if "user_id" not in session:
        return redirect("/")


    colors, tastes, culinaryvalues, categories, healthvalues = query.get_report_strings()
    report_tastes = query.get_report_taste_strings(report_id)
    fetched       = query.get_report_details(report_id)
    symptom_reps  = [ row for row in query.get_report_healthvalues(report_id) ]
    symptom_counts = [ (healthvalue, count_blanched, count_unblanched) 
                    for healthvalue, count_blanched, count_unblanched in symptom_reps ]
    print(healthvalues)
    return render_template("view_report.html", fetched=fetched, colors=colors, 
                           tastes=tastes, culvalues=culinaryvalues, categories=categories, 
                           report_tastes=report_tastes, healthvalues=healthvalues, 
                           symptom_counts=symptom_counts)

@app.route("/view_user/<int:user_id>")
def view_user(user_id):
    if "user_id" not in session:
        return redirect("/")

    user_data = query.get_user_data(user_id)
    if not user_data:
        abort(404)

    user_data = dict(user_data[0])
    if not user_data["lastlogon"]:
        user_data["lastlogon"] = "Never"

    user_report_count = query.get_user_report_count(user_id)

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
        report = query.get_report_details(report_id)
        taste_ids = [ id[0] for id in query.get_report_taste_ids(report_id) ]
    colors, tastes, culinaryvalues, categories, _ = query.get_report_strings()
    return render_template("create_report.html", report=report, colors=colors, tastes=tastes, 
                           culvalues=culinaryvalues, categories=categories, taste_ids=taste_ids)

@app.route("/create_symptom_report/<int:report_id>")
def create_symptom_report(report_id):
    require_login()
    require_report_exists(report_id)

    report = query.get_report_details(report_id)
    report_tastes = query.get_report_taste_strings(report_id)
    colors, tastes, culinaryvalues, categories, healthvalues = query.get_report_strings()
    symptom_reps  = [ row for row in query.get_report_healthvalues(report_id) ]
    symptom_counts = [ (healthvalue, count_blanched, count_unblanched) 
                for healthvalue, count_blanched, count_unblanched in symptom_reps ]
    print(healthvalues)
    return render_template("create_symptom_report.html", fetched=report, colors=colors, 
                        tastes=tastes, culvalues=culinaryvalues, categories=categories, 
                        report_tastes=report_tastes, healthvalues=healthvalues, 
                        symptom_counts=symptom_counts)

@app.route("/send_symptom_report", methods=["POST"])
def send_symptom_report():
    require_login()
    user_id       = session["user_id"]
    report_id     = request.form.get("report_id")
    healthvalue   = request.form.get("healthvalue")
    blanched      = request.form.get("blanched")
    if blanched:
        blanched = 1
    else:
        blanched = 0
    print("symptom report POST", report_id, healthvalue, blanched)
    
    require_report_ownership(report_id)
    if not healthvalue in [str(i) for i in range(1,6)]:
        print(f"not {healthvalue} in range(1,6)")
        if healthvalue == 0:
            return "symptom report deletion not implemented yet"
        abort(418)
    healthvalue_sql = """   INSERT INTO symptomreports
                                (uid, date, report_id, healthvalue, blanched)
                                VALUES (?, datetime('now'), ?, ?, ?) """
    params = (user_id, report_id, healthvalue, blanched)
    db.execute(healthvalue_sql, params)
    return redirect(url_for("view_report", report_id=report_id))

@app.route("/edit_report/<int:report_id>")
def edit_report(report_id):
    require_login()
    owner_id = query.get_report_owner(report_id)
    require_report_ownership(owner_id)
    return create_report(report_id=report_id)


@app.route("/send_report_edit/<int:report_id>", methods=["POST"])
def send_report_edit(report_id):
    require_login()
    require_report_ownership(report_id)

    category_new, color_new, culinaryvalue_new, tastes_new = get_reportform_contents()
    validate_reportform_contents(category_new, color_new, culinaryvalue_new, tastes_new)
    category, color, culinaryvalue, tastes = query.get_report_raw(report_id)
    if not (category == category_new and color == color_new and culinaryvalue == culinaryvalue_new):
        sql = """
            UPDATE reports SET category = ?, color = ?, culinaryvalue = ?
            WHERE id = ?
        """
        db.execute(sql, [category_new, color_new, culinaryvalue_new, report_id])
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
    category, color, culinaryvalue, tastes = get_reportform_contents()
    validate_reportform_contents(category, color, culinaryvalue, tastes)

    uid = session["user_id"]
    sql = """   INSERT INTO reports (uid, date, category, color, culinaryvalue) 
                VALUES (?, datetime('now'), ?, ?, ?) """
    params = [uid, category, color, culinaryvalue]
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

@app.route("/delete_report/<int:report_id>")
def delete_report(report_id):
    require_login()
    owner_id = query.get_report_owner(report_id)
    require_report_ownership(owner_id)

    sql = """
            UPDATE reports SET deleted = 1
            WHERE id = ?
            """
    db.execute(sql, [report_id, ])
    return redirect(url_for("view_report", report_id=report_id))

@app.route("/all_reports")
def all_reports():
    sql = "SELECT * FROM reports"
    reports = db.query(sql)
    return render_template("reports.html", data=reports)

@app.route("/report_fatality/<int:user_id>")
def report_fatality(user_id):
    return "not yet implemented, please contact support"

@app.route("/search", methods=["GET"])
def search():
    require_login()
    keywords = request.args.get("query")
    #TODO: validate input
    #TODO: multiword search how
    result = query.get_search_results(keywords)
    return render_template("search.html", data=result)

@app.route("/create", methods=["POST"])
def create():
    username  = request.form["username"]
    password  = request.form["password1"]
    password2 = request.form["password2"]
    #TODO: validate input
    validate_username(username)
    if password != password2:
        return "Passwords do not match"
    password_hash = generate_password_hash(password)

    try:
        sql = "INSERT INTO users (name, auth) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "Username already taken"

    user_id = query.get_uid_from_username(username)
    session["username"] = username
    session["user_id"] = user_id
    timestamp_login(user_id)
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
        timestamp_login(user_id)
        return redirect(redir)
    else:
        return "Wrong username or password"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

def require_login():
    if "user_id" not in session:
        abort(403)

def require_report_ownership(report_id):
    owner_id = query.get_report_owner(report_id)
    if "user_id" not in session:
        abort(403)
    user_id = session["user_id"]
    if user_id != owner_id:
        print(f"Suspicious activity - require_ownership abort: {user_id} != {owner_id}")
        abort(403)

def get_reportform_contents():
    tastecount    = query.get_availabe_tastes_count()
    category      = request.form["category"]
    color         = request.form["color"]
    tastes = [ i for i in range(1,int(tastecount)+1) if request.form.get(f"taste{i}") ]
    culinaryvalue = request.form["culvalue"]
    
    validate_reportform_contents(category, color, culinaryvalue, tastes)
    
    return (category, color, culinaryvalue, tastes)

def tastes_valid(tastes):
    valid_ids = query.get_valid_taste_ids()
    for id in tastes:
        if id not in valid_ids:
            return f"taste id {id} invalid"
    return True

def validate_username(username):
    allowed_username_characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    if 3 > len(username) > 20:
        return "username must be between 3 and 20 characters"
    for char in username:
        if not char in allowed_username_characters:
            return f"username may only contain {allowed_username_characters}"

def validate_reportform_contents(category, color, culinaryvalue, tastes):
    if not category in [str(i) for i in range(1,16)]:
            abort(418)
    if not color in [str(i) for i in range(1,343)]:
            abort(418)
    if not culinaryvalue in [str(i) for i in range(1,4)]:
            abort(418)
    if not tastes_valid(tastes):
            abort(418)
    if query.report_exists_with(category=category, color=color, culinaryvalue=culinaryvalue, tastes=tastes):
        #TODO
        pass

def require_report_exists(report_id):
    if not query.report_exists(report_id):
        abort(404)

def timestamp_login(user_id):
    sql = """   UPDATE users
                SET lastlogon = datetime('now')
                WHERE id = ? """
    param = (user_id, )
    db.execute(sql, param)
