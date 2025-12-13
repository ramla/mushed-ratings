import db
import settings

class AdvancedSearchQuery:
    def __init__(self, params):
        self.params = settings.ADVANCED_SEARCH_PARAMETERS
        for param in params:
            setattr(self,param,"")
        self.sorting = "date"
        self.descending = False

    def validate(self):
        return False


def get_auth(username):
    sql = """   SELECT auth, id
                FROM users
                WHERE name = ?
            """
    result = db.query(sql, [username])
    if result:
        return result[0]
    return False


def get_availabe_tastes_count():
    return db.query("SELECT COUNT(id) FROM tastes")[0][0]


def get_earliest_symptom_report(report_id, not_from=None):
    sql = """   SELECT sr.uid, sr.date
                FROM symptomreports AS sr
                WHERE sr.report_id = ?
            """
    params = (report_id, )
    if not_from:
        sql += """AND sr.uid != ?
        """
        params = (report_id, not_from)
    end = """   ORDER BY sr.date
            """
    return db.query(sql + end, params)


def get_most_credits():
    sql = """   SELECT id, name, credits AS amount
                FROM users
                ORDER BY credits DESC
        """
    return db.query(sql, [])[0]


def get_most_unique_eaten():
    sql = """   SELECT  u.id,
                        u.name,
                        COUNT(DISTINCT r.report_id) AS amount
                FROM users u
                LEFT JOIN
                    (   SELECT id AS report_id, uid
                            FROM reports
                        UNION
                        SELECT report_id, uid
                            FROM symptomreports
                    ) AS r 
                    ON r.uid = u.id
                GROUP BY u.id
                ORDER BY amount DESC
        """
    return db.query(sql, [])[0]


def get_valid_taste_ids():
    result = db.query("SELECT id FROM tastes")
    id_list = []
    for row in result:
        id_list.append(row[0])
    return id_list


def get_report_strings():
    colors         = db.query("SELECT id, name, hex FROM colors")
    tastes         = get_tastes_strings()
    culinaryvalues = db.query("SELECT id, name, description FROM culinaryvalues")
    categories     = db.query("SELECT id, name FROM categories")
    healthvalues   = db.query("SELECT id, name, description FROM healthvalues")
    return (colors, tastes, culinaryvalues, categories,
            { id: { "name": name,
                    "description": description } 
            for id, name, description in healthvalues } )


def get_tastes_strings():
    return db.query("SELECT id, name, description FROM tastes")


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
    sql = """   SELECT id, deleted
                    FROM reports
                WHERE category = ?
                    AND color = ?
                    AND culinaryvalue = ?
            """
    params = (category, color, culinaryvalue)
    result = db.query(sql, params)

    if len(result) == 0 or taste_ids == []:
        return None

    report_id, deleted = result[0][0], result[0][1]
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
        return (report_id, deleted)
    return None


def get_n_symptom_reports_for(report_id):
    sql = """   SELECT COUNT(1)
                    FROM symptomreports sr
                WHERE sr.report_id = ?
    """
    param = (report_id, )
    return db.query(sql, param)[0][0]


def get_search_results(keywords):
    keywords = "%" + keywords + "%"
    sql = """   SELECT r.id, r.date, r.uid, r.deleted,
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


def get_search_results_advanced(query:AdvancedSearchQuery):
    taste_ids = []
    if query.taste_ids:
        taste_ids = query.taste_ids
    sql_begin = """ SELECT r.id, r.date, r.uid, r.deleted,
                        u.name AS user_name,
                        c.name AS color_name,
                        cat.name AS category_name,
                        cv.name AS culinaryvalue_name,
                        GROUP_CONCAT(rt.tastes_id)    AS taste_ids
                    FROM reports r
                        JOIN users u ON r.uid = u.id
                        JOIN colors c ON r.color = c.id
                        JOIN categories cat ON r.category = cat.id
                        JOIN culinaryvalues cv ON r.culinaryvalue = cv.id
                        JOIN report_tastes rt ON r.id = rt.report_id
                        JOIN tastes t ON t.id = rt.tastes_id
                        """
    sql_where = "WHERE 1=1"
    params = []
    if query.user_name:
        sql_where += "\n                        AND u.name LIKE ?"
        params += [query.user_name]
        print(params)
    if query.date:
        pass
    if query.category_name:
        sql_where += "\n                        AND cat.name LIKE ?"
        params +=  [query.category_name]
        print(params)
    if query.color_name:
        sql_where += "\n                        AND c.name LIKE ?"
        params += [query.color_name]
        print(params)
    if query.culinaryvalue_name:
        sql_where += "\n                        AND cv.name LIKE ?"
        params += [query.culinaryvalue_name]
    if taste_ids:
        # sql_begin += """    JOIN report_tastes rt ON r.id = rt.report_id
        #                     JOIN tastes t ON t.id = rt.tastes_id
        #                 """
        for t_id in taste_ids:
            sql_where += "\n                        AND t.id = ?"
            params += [t_id]
    if query.edibility:
        sql_begin += """    LEFT JOIN symptomreports sr ON r.id = sr.report_id
                            JOIN healthvalues hv ON sr.healthvalue = hv.id
                        """
        sql_where += "\n                        AND hv.name LIKE ?"
        params += [query.edibility]
    if query.deleted == 0:
        sql_where += "\n                        AND deleted = 0"
    elif query.deleted == 1:
        sql_where += "\n                        AND deleted = 1"

    sql_where += """\n                    GROUP BY r.id
                """
    if query.sorting == "edibility":
        sql_begin = """ WITH HealthValueStats AS (
                        SELECT 
                            report_id,
                            AVG(healthvalue) AS avg_healthvalue
                        FROM 
                            symptomreports
                        GROUP BY 
                            report_id)
                    """ + sql_begin + """
                        LEFT JOIN HealthValueStats hvs ON hvs.report_id = r.id
                    """
        sql = sql_begin + sql_where + """
        ORDER BY avg_healthvalue
        """
    else:
        sql = sql_begin + sql_where

    if query.sorting == "date":
        sql += f"ORDER BY r.date {query.descending*"DESC"}"
    elif query.sorting == "id":
        sql += f"ORDER BY r.id {query.descending*"DESC"}"
    elif query.sorting == "user":
        sql += f"ORDER BY u.name {query.descending*"DESC"}"
    elif query.sorting == "category":
        sql += f"ORDER BY cat.name {query.descending*"DESC"}"
    elif query.sorting == "culinary":
        sql += f"ORDER BY cv.name {query.descending*"DESC"}"

    print("\n",sql, "\n\n", params, "\n")
    return db.query(sql, params)


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


def get_user_reports(user_id):
    sql = """   SELECT r.id, r.date, r.deleted,
                c.name AS color_name,
                cat.name AS category_name,
                cv.name AS culinaryvalue_name
                FROM reports r
                    JOIN users u ON r.uid = u.id
                    JOIN colors c ON r.color = c.id
                    JOIN categories cat ON r.category = cat.id
                    JOIN culinaryvalues cv ON r.culinaryvalue = cv.id
                WHERE u.id = ?
            """
    param = (user_id, )
    return db.query(sql, param)


def get_user_symptom_reports(user_id):
    sql = """   SELECT sr.id, sr.report_id, sr.date, sr.healthvalue, sr.blanched,
                        hv.name
                FROM symptomreports AS sr
                    JOIN healthvalues hv ON sr.healthvalue = hv.id
                WHERE sr.uid = ?
                GROUP BY sr.report_id
            """
    param = (user_id, )
    return db.query(sql, param)
