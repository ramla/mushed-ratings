from flask import Flask
from flask import render_template
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    db = sqlite3.connect("database.db")
    db.execute("INSERT INTO visits (visited_at) VALUES (datetime('now'))")
    db.commit()
    result = db.execute("SELECT COUNT(*) FROM visits").fetchone()
    count = result[0]
    db.close()
    paragraph = "Sivua on ladattu " + str(count) + " kertaa"
    return render_template("index.html", second_p=paragraph)

@app.route("/page/<int:page_id>")
def page(page_id):
    return "Tämä on sivu " + str(page_id)
