import sqlite3
from pathlib import Path
from flask import g


def get_connection():
    create_new = False
    dbfile = Path("database.db")
    if not dbfile.is_file():
        create_new = True
    con = sqlite3.connect("database.db")
    if create_new:
        with open("schema.sql", "r", encoding="utf-8") as schema_file:
            schema = schema_file.read()
            cursor = con.cursor()
            cursor.executescript(schema)
            con.commit()
        with open("init.sql", "r", encoding="utf-8") as init_file:
            init_db = init_file.read()
            cursor = con.cursor()
            cursor.executescript(init_db)
            con.commit()
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con


def execute(sql, params=None):
    if params is None:
        params = []
    con = get_connection()
    result = con.execute(sql, params)
    con.commit()
    g.last_insert_id = result.lastrowid
    con.close()


def last_insert_id():
    return g.last_insert_id


def query(sql, params=None):
    if params is None:
        params = []
    con = get_connection()
    result = con.execute(sql, params).fetchall()
    con.close()
    return result
