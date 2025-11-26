import db


def get_auth(username):
    sql = """   SELECT auth, id 
                FROM users 
                WHERE name = ?
            """
    password_hash, user_id = db.query(sql, [username])[0]
    return password_hash, user_id

def get_availabe_tastes_count():
    return db.query("SELECT COUNT(id) FROM tastes")[0][0]

def get_valid_taste_ids():
    result = db.query("SELECT id FROM tastes")
    id_list = []
    for row in result:
        id_list.append(row[0])
    return id_list

def get_report_strings():
    colors         = db.query("SELECT id, name, hex FROM colors")
    tastes         = db.query("SELECT id, name, description FROM tastes")
    culinaryvalues = db.query("SELECT id, name, description FROM culinaryvalues")
    categories     = db.query("SELECT id, name FROM categories")
    healthvalues   = db.query("SELECT id, name, description FROM healthvalues")
    return (colors, tastes, culinaryvalues, categories, 
            { id: { "name": name,
                    "description": description } 
            for id, name, description in healthvalues } )


def get_report_owner(report_id):
    param = (report_id, )
    sql = """ SELECT uid FROM reports WHERE reports.id = ?"""
    result = db.query(sql, param)
    if not result:
        return None
    return result[0][0]


def get_report_details(report_id):
    param = (report_id, )
    report_sql = """SELECT r.id, r.date, r.category, r.color, r.deleted,
                    u.name AS user_name,
                    u.id AS user_id,
                    c.name AS color_name,
                    c.hex AS color_hex,
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


def get_report_healthvalues(report_id):
    healthvalue_sql = """
    SELECT healthvalue,
        COUNT(CASE WHEN blanched = 1 THEN 1 END) AS blanched_count,
        COUNT(CASE WHEN blanched = 0 THEN 1 END) AS unblanched_count
    FROM symptomreports
    WHERE report_id = ? 
        AND deleted = 0 
        AND healthvalue BETWEEN 0 AND 5
    GROUP BY healthvalue
    
    UNION ALL

    -- Total counts
    SELECT NULL AS healthvalue,
        SUM(CASE WHEN blanched = 1 THEN 1 ELSE 0 END) AS blanched_count,
        SUM(CASE WHEN blanched = 0 THEN 1 ELSE 0 END) AS unblanched_count
    FROM symptomreports
    WHERE report_id = ?
        AND deleted = 0
        AND healthvalue BETWEEN 0 AND 5
    ORDER BY healthvalue
    """
    param = (report_id, report_id)
    return db.query(healthvalue_sql, param)


def get_report_taste_strings(report_id):
    taste_sql =  """SELECT t.id, t.name
                    FROM tastes t
                        JOIN report_tastes rt ON t.id = rt.tastes_id
                        JOIN reports r        ON r.id = rt.report_id
                    WHERE r.id = ?"""
    param = (report_id,)
    return db.query(taste_sql, param)


def get_report_taste_ids(report_id):
    taste_sql =  """SELECT t.id
                    FROM tastes t
                        JOIN report_tastes rt ON t.id = rt.tastes_id
                        JOIN reports r        ON r.id = rt.report_id
                    WHERE r.id = ?"""
    param = (report_id,)
    return db.query(taste_sql, param)


def get_report_raw(report_id):
    param = (report_id, )
    report_sql = """SELECT r.category, r.color, r.culinaryvalue
                    FROM reports r
                        JOIN users u ON r.uid = u.id
                        JOIN colors c ON r.color = c.id
                        JOIN categories cat ON r.category = cat.id
                        JOIN culinaryvalues cv ON r.culinaryvalue = cv.id
                    WHERE r.id = ?"""
    category, color, culinaryvalue = db.query(report_sql, param)[0]
    tastes = get_report_taste_ids(report_id)
    return (category, color, culinaryvalue, tastes)


def report_exists(report_id):
    param = (report_id, )
    sql = """SELECT 1 FROM reports
                WHERE reports.id = ?
                    AND reports.deleted = 0"""
    return db.query(sql, param)


def report_exists_with(category, color, culinaryvalue, taste_ids):
    sql = """   SELECT id
                    FROM reports
                WHERE category = ?
                    AND color = ?
                    AND culinaryvalue = ?
            """
    params = (category, color, culinaryvalue)
    result = db.query(sql, params)
    
    if len(result) == 0 or taste_ids == []:
        return None
    
    report_id = result[0][0]
    sql = """   SELECT 1
                    FROM report_tastes
                WHERE report_id = ?
                    AND 
                        (tastes_id = ?
            """
    for _ in range(1, len(taste_ids)):
        sql += "\n OR tastes_id = ?"
    sql += ")"
    matches = db.query(sql, [report_id] + taste_ids)
    if len(matches) == len(taste_ids):
        return report_id
    return None

def get_search_results(keywords):
    keywords = "%" + keywords + "%"
    sql = """   SELECT r.id, r.date, r.uid,
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
                    OR cv.name LIKE LOWER(?)
                    OR r.date LIKE LOWER(?)
            """
    return db.query(sql, [keywords, keywords, keywords, keywords, keywords])


def get_uid_from_username(username):
    sql = "SELECT id FROM users WHERE name = ?"
    return db.query(sql, [username])[0][0]


def get_user_data(user_id):
    param = str(user_id)
    sql_user_data = """         SELECT id, name, lastlogon, credits FROM users
                                WHERE id = ?
    """
    return db.query(sql_user_data, param)


def get_user_report_count(user_id):
    param = (user_id, )
    sql_user_report_count = """ SELECT COUNT(id) FROM reports
                                WHERE reports.uid = ?
                                    AND reports.deleted = 0
    """
    return db.query(sql_user_report_count, param)[0][0]
