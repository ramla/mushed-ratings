from flask import Flask, url_for
from flask import redirect, render_template, request, session, abort, flash
from werkzeug.security import generate_password_hash, check_password_hash
import db
import config
import crud
import query
import secrets

app = Flask(__name__)
app.secret_key = config.secret_key
REPORT_REWARD       = 15
SYMPTOM_REWARD      = 10
SYMPTOM_REWARD_MIN  = 2
SYMPTOM_REWARD_DIMINISHING_MULTIPLIER = 1
TESTING = True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", filled={})
    
    if request.method == "POST":
        valid = True
        username  = request.form["username"]
        if not validate_username(username):
            valid = False

        password  = request.form["password1"]
        password2 = request.form["password2"]
        if not validate_password(password, password2):
            valid = False
        
        if not valid:
            filled = { "username": username }
            return render_template("register.html", filled=filled)
        else:
            password_hash = generate_password_hash(password)
            crud.create_user(username, password_hash)
            user_id = query.get_uid_from_username(username)
            session["csrf_token"] = secrets.token_hex(16)
            session["username"] = username
            session["user_id"] = user_id
            crud.timestamp_login(user_id)
            flash("Account created successfully")
            return redirect("/")

@app.route("/view_report/<int:report_id>")
def view_report(report_id):
    logged_in = require_login()
    if not logged_in:
        return redirect("/")

    colors, tastes, culinaryvalues, categories, healthvalues = query.get_report_strings()
    report_tastes = query.get_report_taste_strings(report_id)
    fetched       = query.get_report_details(report_id)
    symptom_reps  = [ row for row in query.get_report_healthvalues(report_id) ]
    symptom_counts = [ (healthvalue, count_blanched, count_unblanched) 
                    for healthvalue, count_blanched, count_unblanched in symptom_reps ]
    
    taste_ids = [taste[0] for taste in report_tastes]
    query.report_exists_with(fetched["category"],fetched["color"],fetched["culinaryvalue_id"],taste_ids)
    
    return render_template("view_report.html", fetched=fetched, colors=colors, 
                           tastes=tastes, culvalues=culinaryvalues, categories=categories, 
                           report_tastes=report_tastes, healthvalues=healthvalues, 
                           symptom_counts=symptom_counts)

@app.route("/view_user/<int:user_id>")
def view_user(user_id):
    logged_in = require_login()
    if not logged_in:
        return redirect("/")

    user_data = query.get_user_data(user_id)
    if not user_data:
        abort(404)
    user_reports = query.get_user_reports(user_id)
    user_symptom_reports = query.get_user_symptom_reports(user_id)

    

    user_data = dict(user_data[0])
    if not user_data["lastlogon"]:
        user_data["lastlogon"] = "Never"

    #user_report_count = query.get_user_report_count(user_id)

    return render_template("view_user.html", user=user_data, reports=user_reports, symptom_reports=user_symptom_reports)

#TODO: potential DoS surface for registered users
@app.route("/create_report/")
def create_report(report_id=None):
    taste_ids = []
    logged_in = require_login()
    if not logged_in:
        return redirect("/")
    if report_id is None:
        report = None
    else:
        report = query.get_report_details(report_id)
        taste_ids = [ id["id"] for id in query.get_report_taste_ids(report_id) ]
    colors, tastes, culinaryvalues, categories, _ = query.get_report_strings()
    return render_template("create_report.html", report=report, colors=colors, tastes=tastes, 
                           culvalues=culinaryvalues, categories=categories, taste_ids=taste_ids)

@app.route("/create_symptom_report/<int:report_id>")
def create_symptom_report(report_id):
    logged_in = require_login()
    if not logged_in:
        return redirect("/")
    require_report_exists(report_id)

    report = query.get_report_details(report_id)
    report_tastes = query.get_report_taste_strings(report_id)
    colors, tastes, culinaryvalues, categories, healthvalues = query.get_report_strings()
    symptom_reps  = [ row for row in query.get_report_healthvalues(report_id) ]
    symptom_counts = [ (healthvalue, count_blanched, count_unblanched) 
                    for healthvalue, count_blanched, count_unblanched in symptom_reps ]

    return render_template("create_symptom_report.html", fetched=report, colors=colors, 
                        tastes=tastes, culvalues=culinaryvalues, categories=categories, 
                        report_tastes=report_tastes, healthvalues=healthvalues, 
                        symptom_counts=symptom_counts)

@app.route("/send_symptom_report", methods=["POST"])
def send_symptom_report():
    if not logged_in:
        return redirect("/")
    check_csrf()
    user_id       = session["user_id"]
    report_id     = request.form.get("report_id")
    require_report_exists(report_id)

    healthvalue   = request.form.get("healthvalue")
    blanched      = request.form.get("blanched")
    error = validate_symptomform_contents(healthvalue, blanched)
    if error:
        return error
    n_symptom_reports = query.get_n_symptom_reports_for(report_id)
    reward = max(SYMPTOM_REWARD_MIN, SYMPTOM_REWARD - int((SYMPTOM_REWARD_DIMINISHING_MULTIPLIER * n_symptom_reports)))
    crud.insert_symptom_report(user_id, report_id, healthvalue, blanched, reward)

    crud.update_user_credits(user_id, reward)

    return redirect(url_for("view_report", report_id=report_id))

@app.route("/edit_report/<int:report_id>")
def edit_report(report_id):
    logged_in = require_login()
    if not logged_in:
        return redirect("/")
    owner_id = query.get_report_owner(report_id)
    require_report_ownership(owner_id)
    return create_report(report_id=report_id)


@app.route("/send_report_edit/<int:report_id>", methods=["POST"])
def send_report_edit(report_id):
    logged_in = require_login()
    if not logged_in:
        return redirect("/")
    check_csrf()
    if not query.report_exists(report_id):
        abort(404)
    require_report_ownership(report_id)

    category_new, color_new, culinaryvalue_new, tastes_new = get_reportform_contents()
    identical_report = validate_reportform_contents(category_new, color_new, culinaryvalue_new, tastes_new)
    #TODO: Annul credits and delete if edited undeleted mushroom exists
    
    category, color, culinaryvalue, tastes = query.get_report_raw(report_id)

    if not (category == category_new and color == color_new and culinaryvalue == culinaryvalue_new):
        crud.update_report(category_new, color_new, culinaryvalue_new, report_id)
    if not tastes == tastes_new:
        crud.update_report_tastes(report_id, tastes_new)
    
    return redirect(url_for("view_report", report_id=report_id))


@app.route("/send_report", methods=["POST"])
def send_report():
    logged_in = require_login()
    if not logged_in:
        return redirect("/")
    check_csrf()
    category, color, culinaryvalue, tastes = get_reportform_contents()
    identical_report = validate_reportform_contents(category, color, culinaryvalue, tastes)
    if identical_report:
        return identical_report
    
    uid = session["user_id"]
    crud.insert_report(uid, category, color, culinaryvalue)
    
    report_id = db.last_insert_id()
    crud.insert_tastes(report_id, tastes)

    crud.update_user_credits(uid, REPORT_REWARD)

    return redirect(url_for("view_report", report_id=report_id))

@app.route("/delete_report/<int:report_id>")
def delete_report(report_id):
    logged_in = require_login()
    if not logged_in:
        return redirect("/")
    owner_id = query.get_report_owner(report_id)
    require_report_ownership(owner_id)

    crud.set_report_deleted(report_id)

    crud.update_user_credits(owner_id, -REPORT_REWARD)

    return redirect(url_for("view_report", report_id=report_id))

#TODO: make this obsolete
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
    logged_in = require_login()
    if not logged_in:
        return redirect("/")
    keywords = request.args.get("query")
    #TODO: validate input
    #TODO: multiword search how
    result = query.get_search_results(keywords)
    return render_template("search.html", data=result)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    redir    = request.form["redirect"]
    
    password_hash, user_id = query.get_auth(username)

    if check_password_hash(password_hash, password):
        session["csrf_token"] = secrets.token_hex(16)
        session["user_id"] = user_id
        session["username"] = username
        crud.timestamp_login(user_id)
        return redirect(redir)
    else:
        return "Wrong username or password"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

def require_login():
    if "user_id" not in session:
        flash("Please log in or sign up")
        return False
    return True

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
    category      = request.form.get("category")
    color         = request.form.get("color")
    tastes = [ i for i in range(1,int(tastecount)+1) if request.form.get(f"taste{i}") ]
    culinaryvalue = request.form.get("culvalue")
    
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
    valid = True
    if 3 > len(username) > 20:
        flash("Username must be between 3 and 20 characters")
        valid = False
    for char in username:
        if not char in allowed_username_characters:
            flash(f"Username may only contain {allowed_username_characters}")
            valid = False
            break
    return valid

def validate_password(a, b):
    valid = True
    if a != b:
        flash("Passwords do not match")
        valid = False
    if TESTING:
        if len(a) == 0 or len(b) == 0:
            flash("Password may not be empty")
            valid = False
    else:
        if len(a) < 8 or len(b) < 8:
            flash("Password must be 8 characters or longer")
            valid = False
            #TODO even stronger password
    return valid

def validate_reportform_contents(category, color, culinaryvalue, tastes):
    if not category in [str(i) for i in range(1,16)]:
        abort(418)
    if not color in [str(i) for i in range(1,343)]:
        abort(418)
    if not culinaryvalue in [str(i) for i in range(1,4)]:
        abort(418)
    if not tastes_valid(tastes):
        abort(418)
    identical_report = query.report_exists_with(category=category, color=color, culinaryvalue=culinaryvalue, taste_ids=tastes)
    if not identical_report == None:
        return f"identical report already exists: Report {identical_report}"
    return None

def require_report_exists(report_id):
    if not query.report_exists(report_id):
        abort(404)

def validate_symptomform_contents(healthvalue, blanched):
    if not healthvalue in [str(i) for i in range(1,6)]:
        print(healthvalue)
        if healthvalue == 5:
            return "value not yet in use"
        abort(418)
    print(blanched)
    if not (blanched == "0" or blanched == "1"):
        abort(418)

def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)
