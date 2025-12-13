import secrets
from flask import Flask, url_for
from flask import redirect, render_template, request, session, abort, flash
from werkzeug.security import generate_password_hash, check_password_hash
import db
import config
import crud
import query
import settings

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

@app.route("/")
def index():
    top = { "shrooms": { "amount": 0},
            "credits": { "amount": 0}
        }
    if "username" in session:
        top["credits"] = query.get_most_credits()
        top["shrooms"] = query.get_most_unique_eaten()
    return render_template("index.html", top=top)

@app.route("/register", methods=["GET", "POST"])
def register():
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
            filled = { "username": username,
                       "password1": password,
                       "password2": password2 }
            return render_template("register.html", filled=filled)
        password_hash = generate_password_hash(password)
        error = crud.create_user(username, password_hash)
        if error:
            flash(error)
            filled = { "username": username,
                       "password1": password,
                       "password2": password2 }
            return render_template("register.html", filled=filled)
        user_id = query.get_uid_from_username(username)
        session["csrf_token"] = secrets.token_hex(16)
        session["username"] = username
        session["user_id"] = user_id
        crud.timestamp_login(user_id)
        flash("Account created successfully")
        return redirect("/")

    return render_template("register.html", filled={})

@app.route("/view_report/<int:report_id>")
def view_report(report_id):
    logged_in = require_login()
    if not logged_in:
        return redirect("/")

    colors, tastes, culinaryvalues, categories, healthvalues = query.get_report_strings()
    report_tastes = query.get_report_taste_strings(report_id)
    fetched       = query.get_report_details(report_id)
    symptom_counts  = list(query.get_report_healthvalues(report_id))

    taste_ids = [taste[0] for taste in report_tastes]
    query.report_exists_with(fetched["category"],fetched["color"],
                             fetched["culinaryvalue_id"],taste_ids)

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

    return render_template("view_user.html", user=user_data, reports=user_reports,
                            symptom_reports=user_symptom_reports)

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
    symptom_counts  = list(query.get_report_healthvalues(report_id))

    return render_template("create_symptom_report.html", fetched=report, colors=colors,
                        tastes=tastes, culvalues=culinaryvalues, categories=categories,
                        report_tastes=report_tastes, healthvalues=healthvalues,
                        symptom_counts=symptom_counts)

@app.route("/send_symptom_report", methods=["POST"])
def send_symptom_report():
    logged_in = require_login()
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
    reward = max(settings.SYMPTOM_REWARD_MIN, settings.SYMPTOM_REWARD
                  - int((settings.SYMPTOM_REWARD_DIMINISHING_MULTIPLIER * n_symptom_reports)))
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
    session_user = session["user_id"]

    category_new, color_new, culinaryvalue_new, tastes_new = get_reportform_contents()
    identical_report = validate_reportform_contents(category_new, color_new,
                                                    culinaryvalue_new, tastes_new)
    # handle case of other user posted symptom reports
    original_not_needed = not other_user_posted_symptom_reports(report_id, session_user)
    if identical_report:
        identical_report_id = identical_report[1][0]
        # Annul credits,
        crud.update_user_credits(session_user, -settings.REPORT_REWARD)
        # in case of user reported symptoms:
        # update session_users symptom reports to point to found identical_report
        crud.move_symptom_reports(report_id, identical_report_id, session_user)
        # delete original report if it's not needed:
        if original_not_needed:
            crud.set_report_deleted(report_id)
    else:
        category, color, culinaryvalue, tastes = query.get_report_raw(report_id)
        if original_not_needed:
            # just edit report
            if not (category == category_new and color == color_new
                    and culinaryvalue == culinaryvalue_new):
                crud.update_report(category_new, color_new, culinaryvalue_new, report_id)
            if not tastes == tastes_new:
                crud.update_report_tastes(report_id, tastes_new)
        else:
            # create new report
            crud.insert_report(session_user, category, color, culinaryvalue)
            new_report_id = db.last_insert_id()
            crud.insert_tastes(new_report_id, tastes_new)
            return redirect(url_for("view_report", report_id=new_report_id))
    return redirect(url_for("view_report", report_id=report_id))


@app.route("/send_report", methods=["POST"])
def send_report():
    logged_in = require_login()
    if not logged_in:
        return redirect("/")
    check_csrf()
    uid = session["user_id"]
    category, color, culinaryvalue, tastes = get_reportform_contents()
    identical_report = validate_reportform_contents(category, color, culinaryvalue, tastes)
    if identical_report:
        error = identical_report[0]
        identical_report_id, deleted = identical_report[1][0], identical_report[1][1]

        if deleted == 0:
            return error
        crud.update_report_uid(identical_report_id, uid)
        return redirect(url_for("view_report", report_id=identical_report_id))

    crud.insert_report(uid, category, color, culinaryvalue)
    report_id = db.last_insert_id()
    crud.insert_tastes(report_id, tastes)
    crud.update_user_credits(uid, settings.REPORT_REWARD)
    return redirect(url_for("view_report", report_id=report_id))

@app.route("/delete_report", methods=["POST"])
def delete_report():
    logged_in = require_login()
    check_csrf()
    if not logged_in:
        return redirect("/")
    report_id = request.form.get("report_id")
    owner_id = query.get_report_owner(report_id)
    require_report_ownership(owner_id)
    if not other_user_posted_symptom_reports(report_id, owner_id):
        crud.set_report_deleted(report_id)
    crud.update_user_credits(owner_id, -settings.REPORT_REWARD)
    crud.set_symptom_reports_deleted(report_id, owner_id)

    return redirect(url_for("view_report", report_id=report_id))

@app.route("/report_fatality/<int:user_id>")
def report_fatality(user_id):
    print(f"unimplemented: fatality reported of user {user_id}")
    return "not yet implemented, please contact support"

@app.route("/search", methods=["GET"])
def search():
    logged_in = require_login()
    if not logged_in:
        return redirect("/")
    keywords = request.args.get("query")
    result = query.get_search_results(keywords)
    return render_template("search.html", data=result)

@app.route("/advsearch", methods=["GET", "POST"])
def advanced_search():
    logged_in = require_login()
    if not logged_in:
        return redirect("/")

    result = {}
    empty_query = True
    tastes = {}
    taste_data = []
    q = query.AdvancedSearchQuery(settings.ADVANCED_SEARCH_PARAMETERS)
    if request.method == "POST":
        check_csrf()

        for param in settings.ADVANCED_SEARCH_PARAMETERS:
            setattr(q, param, request.form.get(param))
            if getattr(q, param):
                empty_query = False
        q.sorting = request.form.get("sorting")
        desc_val = request.form.get("descending")
        q.descending = desc_val in ("1", "true", "True")
        error = q.validate()
        if error:
            flash(error)
            return render_template("search_advanced.html", filled=q)

        if not empty_query:
            tastestrings = query.get_tastes_strings()
            for i, row in enumerate(tastestrings):
                tastes[str(i+1)] = row["name"]
            result = query.get_search_results_advanced(q)
            for row in result:
                row_taste_ids = row["taste_ids"].split(",")
                taste_data.append(row_taste_ids)

    return render_template("search_advanced.html", filled=q, data=result, tastes=tastes,
                           taste_data=taste_data)

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

    return (category, color, culinaryvalue, tastes)

def tastes_valid(tastes):
    valid_ids = query.get_valid_taste_ids()
    for taste_id in tastes:
        if taste_id not in valid_ids:
            return f"taste id {taste_id} invalid"
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
    if settings.TESTING:
        if len(a) == 0 or len(b) == 0:
            flash("Password may not be empty")
            valid = False
    else:
        if len(a) < 8 or len(b) < 8:
            flash("Password must be 8 characters or longer")
            valid = False
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
    identical_report = query.report_exists_with(category=category, color=color,
                                                culinaryvalue=culinaryvalue, taste_ids=tastes)
    if not identical_report is None:
        return (f"identical report already exists: Report {identical_report}", identical_report)
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
    if not blanched in ("0", "1"):
        abort(418)
    return None

def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

def other_user_posted_symptom_reports(report_id, session_user):
    # in case other users posted symptom reports: find first other user
    sreport = query.get_earliest_symptom_report(report_id, not_from=session_user)
    if sreport:
        first_other_user_id = sreport[0]["uid"]
        # update report uid to first other user with symptom report
        crud.update_report_uid(report_id, first_other_user_id)
        # add report credits to that first other user
        crud.update_user_credits(first_other_user_id, settings.REPORT_REWARD)
        return True
    return False
