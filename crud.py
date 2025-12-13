import sqlite3
import db


def create_user(username, password_hash):
    try:
        sql = """   INSERT INTO users
                        (name, auth) 
                        VALUES (?, ?)
                """
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "Username already taken"
    return None


def insert_report(uid, category, color, culinaryvalue):
    sql = """   INSERT INTO reports
                    (uid, date, category, color, culinaryvalue) 
                    VALUES (?, datetime('now'), ?, ?, ?) 
            """
    params = [uid, category, color, culinaryvalue]
    db.execute(sql, params)


def insert_tastes(report_id, tastes):
    sql = """   INSERT INTO report_tastes
                    (report_id, tastes_id) 
                VALUES (?, ?)
            """
    tastes_inserted = 0
    for i in tastes:
        tastes_inserted += 1
        db.execute(sql, [report_id, i])
    if tastes_inserted == 0:
        db.execute(sql, [report_id, 1]) # mild


def insert_symptom_report(user_id, report_id, healthvalue, blanched, reward):
    sql = """   INSERT INTO symptomreports
                    (uid, date, report_id, healthvalue, blanched, rewarded)
                    VALUES (?, datetime('now'), ?, ?, ?, ?) 
            """
    params = (user_id, report_id, healthvalue, blanched, reward)
    db.execute(sql, params)


def move_symptom_reports(from_report_id, to_report_id, user_id):
    sql = """   UPDATE symptomreports
                    SET report_id = ?
                WHERE report_id = ?
                    AND uid = ?
            """
    params = (to_report_id, from_report_id, user_id)
    db.execute(sql, params)


def set_report_deleted(report_id):
    sql = """
            UPDATE reports 
                SET deleted = 1
            WHERE id = ?
        """
    db.execute(sql, [report_id, ])


def set_symptom_reports_deleted(report_id, user_id):
    sql = """   UPDATE symptomreports
                    SET deleted = 1
                WHERE report_id = ?
                    AND uid = ?
            """
    params = (report_id, user_id)
    db.execute(sql, params)


def timestamp_login(user_id):
    sql = """   UPDATE users
                    SET lastlogon = datetime('now')
                WHERE id = ? """
    param = (user_id, )
    db.execute(sql, param)


def update_user_credits(user_id, amount):
    sql = """   UPDATE users
                    SET credits = credits + ?
                WHERE users.id = ?
                """
    params = (amount, user_id)
    db.execute(sql, params)


def update_report(category, color, culinaryvalue, report_id):
    sql = """   UPDATE reports
                    SET category = ?, color = ?, culinaryvalue = ?
                WHERE id = ?
            """
    db.execute(sql, [category, color, culinaryvalue, report_id])


def update_report_uid(report_id, user_id):
    sql = """   UPDATE reports
                    SET uid = ?, deleted = 0, date = datetime('now')
                WHERE id = ?"""
    params = (user_id, report_id)
    db.execute(sql, params)


def update_report_tastes(report_id, tastes):
    delete_tastes_sql = """ DELETE FROM report_tastes
                            WHERE report_id = ?
                        """
    db.execute(delete_tastes_sql, [report_id, ])

    insert_tastes(report_id, tastes)
